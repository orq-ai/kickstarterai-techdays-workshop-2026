"""Regression eval: `make regression-eval VERSION=2.0.0` (or `uv run python -m evals.regression`).

What it does: reads every row of your orq dataset `<seat>-refund-eval` (seeded from
app/data/dataset.jsonl), sends each customer message to `agent/<seat>-refund-agent@<version>`,
scores the answer and the tool results with evals/scorers.py, and takes the mean pass rate per
scorer.

Exit codes: 0 means every threshold passed, 1 means a threshold was missed, and 2 means
an execution or scoring error prevented a complete evaluation. This is a regression gate,
not a benchmark: the bars say "no worse than the version we shipped", with a margin so the
model's own variance does not flake a green run. Its exit code makes it usable as a CI gate.

Every run is also an Experiment in the Studio, next to the previous ones, with per-row verdicts.
The same detail lands in evals/results/<version>.json.
"""

# isort: skip_file
# app.refund_agent.config must load .env before evaluatorq is imported (it reads ORQ_API_KEY then)
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime

from app.refund_agent.config import ROOT, settings  # loads .env first

from evaluatorq import DataPoint, DatasetIdInput, evaluatorq, job

from app.refund_agent.client import ask_agent, make_orq
from app.refund_agent.entities import ensure_dataset
from evals.scorers import EVALUATORS

# Calibrated on 2026-10-14, gpt-6-luna, managed agent with code tools, 20 rows:
#   v1.0.0 (first draft)   0.95 / 0.85 / 0.95 / 0.70  -> fails attempts and PII
#   v2.0.0 (reference fix) 0.95 / 0.95 / 1.00 / 0.90  -> passes
# The judge bar sits low on purpose: an LLM judge lands near any bar often enough to flake.
THRESHOLDS = {
    "refund_outcome": 0.85,
    "no_unauthorized_attempt": 0.90,  # v2 once called issue_refund on a made-up order id
    "no_pii_leak": 1.00,
    "policy_judge": 0.70,
}
RESULTS_DIR = ROOT / "evals" / "results"


def rows_detail(results) -> list[dict]:
    """Preserve execution and scoring errors separately from quality verdicts."""
    records = []
    for datapoint_result in results:
        inputs = datapoint_result.data_point.inputs
        for job_result in datapoint_result.job_results or [None]:
            output = job_result.output if job_result else None
            output = output if isinstance(output, dict) else {"answer": str(output or "")}
            scores = {}
            for score in (job_result.evaluator_scores or []) if job_result else []:
                error = score.error
                passed = None
                if not error and score.score is not None:
                    passed = score.score.pass_
                    if passed is None and score.score.value is not None:
                        passed = bool(score.score.value)
                if passed is None and not error:
                    error = "Scorer returned no verdict"
                scores[score.evaluator_name] = {
                    "pass": passed,
                    "error": str(error) if error else None,
                    "explanation": str(error or getattr(score.score, "explanation", None) or "")[:300],
                }
            error = datapoint_result.error or (job_result.error if job_result else "No job result returned")
            if not error:
                for name in THRESHOLDS:
                    scores.setdefault(name, {"pass": None, "error": "Scorer result missing", "explanation": ""})
            records.append({
                "message": inputs.get("message"),
                "expected_decision": inputs.get("expected_decision"),
                "tool_calls": output.get("tool_calls", []),
                "answer": output.get("answer", ""),
                "trace_id": output.get("trace_id"),
                "error": str(error) if error else None,
                "scores": scores,
            })
    return records


def means(rows: list[dict]) -> dict[str, float | None]:
    """Only report a scorer's mean when every row has a usable verdict."""
    scores = {}
    for name in THRESHOLDS:
        usable = [row["scores"].get(name) for row in rows if not row["error"]]
        complete = bool(rows) and len(usable) == len(rows) and all(
            score and not score.get("error") and score["pass"] is not None for score in usable
        )
        scores[name] = round(sum(bool(score["pass"]) for score in usable) / len(rows), 3) if complete else None
    return scores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", default=os.environ.get("VERSION") or "2.0.0", help="agent version, or latest")
    parser.add_argument("--parallelism", type=int, default=4)
    args = parser.parse_args(argv)
    settings.require_seat()
    orq = make_orq()

    # ── Step 1 · Run the agent over the orq dataset ──
    # The rows come from orq, not from the local file: edit them in the Studio and the next run
    # uses your edits. Each row is one fresh conversation with the pinned version.
    dataset_id = ensure_dataset(orq)

    @job("refund-agent")
    async def run_agent(datapoint: DataPoint, index: int) -> dict:
        turn = await asyncio.to_thread(
            ask_agent,
            datapoint.inputs["message"],
            args.version,
            orq,
            metadata={"tag": "regression", "expected": datapoint.inputs.get("expected_decision", "")},
        )
        return {
            "answer": turn.answer,
            "tool_calls": [vars(call) for call in turn.tool_calls],
            "trace_id": turn.trace_id,
        }

    url_out: list[str] = []
    name = settings.key("refund-regression")
    results = asyncio.run(
        evaluatorq(
            name,
            data=DatasetIdInput(dataset_id=dataset_id),
            jobs=[run_agent],
            evaluators=EVALUATORS,
            parallelism=args.parallelism,
            print_results=True,
            description=f"agent/{settings.agent_key}@{args.version}",
            path=settings.path,  # in the seat's project: a project-scoped key cannot open it elsewhere
            _experiment_url_out=url_out,
        )
    )

    # ── Step 2 · Compare each mean with its threshold ──
    rows = rows_detail(results)
    errors = []
    if not rows:
        errors.append("No dataset rows returned; run make seed-eval and try again")
    for index, row in enumerate(rows, 1):
        if row["error"]:
            errors.append(f"row {index}: {row['error']}")
        else:
            for name, score in row["scores"].items():
                if score.get("error"):
                    errors.append(f"row {index}, {name}: {score['error']}")
    scores = means(rows)
    failed = [name for name, bar in THRESHOLDS.items() if scores[name] is not None and scores[name] < bar]
    verdict = "error" if errors else "failed" if failed else "passed"
    url = url_out[0] if url_out else ""

    # ── Step 3 · Write the results, print the verdict, return the exit code ──
    out = RESULTS_DIR / f"{args.version}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "agent": f"{settings.agent_key}@{args.version}",
                "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "rows": len(rows),
                "scores": scores,
                "thresholds": THRESHOLDS,
                "failed": failed,
                "errors": errors,
                "verdict": verdict,
                "experiment_url": url,
                "details": rows,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"── Regression eval · {settings.agent_key}@{args.version} ".ljust(55, "─"))
    print(f"rows     : {len(rows)} from dataset {settings.key('refund-eval')}")
    for scorer, bar in THRESHOLDS.items():
        if scores[scorer] is None:
            print(f"error    : {scorer} — incomplete; no mean reported")
        else:
            status = "fail" if scorer in failed else "pass"
            print(f"{status:<8} : {scorer} {scores[scorer]:.2f} (threshold {bar:.2f})")
    print(f"results  : {out.relative_to(ROOT)}")
    if url:
        print(f"studio   : {url}")
    if errors:
        for error in errors:
            print(f"error    : {error}")
        print("verdict  : error, evaluation incomplete; resolve errors and rerun (exit 2)")
        return 2
    if failed:
        print(f"verdict  : failed, {', '.join(failed)} below threshold (exit 1)")
        return 1
    print("verdict  : passed, every scorer at or above its threshold (exit 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
