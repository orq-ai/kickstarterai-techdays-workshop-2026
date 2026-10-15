# Improve and Evaluate · Part B: Prove it with an eval

| | |
|---|---|
| **Prerequisites** | [Part A](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/04/) done: v2.0.0 published |
| **You will have** | a regression eval on an orq.ai dataset that passes v2 and fails v1, and its Experiment in the Studio |

## Why

Replays and simulations show that v2 behaves differently on the cases you picked. They cannot show that nothing else broke. A fixed dataset, scored the same way every time, can: it turns "looks fixed" into a pass or fail you can rerun on every change.

Read the [Concepts](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/04-concepts/) page for scorer design and the evaluation gate.

## Steps

### Step 1 · Create evaluation resources

Create the dataset and the judge the regression eval uses:

```bash {.terminal}
uv run python -m app.refund_agent.entities seed-eval
```

This creates the dataset from [`app/data/dataset.jsonl`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/data/dataset.jsonl) and the boolean policy judge from [`app/data/judge_prompt.md`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/data/judge_prompt.md). Existing resources are left unchanged. `make seed-eval` is the optional shortcut. Example session (your seat and entity IDs will differ):

<!-- termynal -->

```console
$ uv run python -m app.refund_agent.entities seed-eval
── Seed · create this seat's evaluation resources ────
seat     : ws07 → <your project>/workshop
dataset  : ws07-refund-eval (01M4…)
judge    : ws07-refund-policy-judge (01M4…)
```

**The SDK calls behind seed-eval.** 
The dataset is created once, then populated from the local JSONL rows. The judge is a separate boolean evaluator resource that stores its prompt and model configuration in orq.ai. [`seed_eval()`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/refund_agent/entities.py#L413-L426) runs both.

**Dataset.** The two calls below are in [`ensure_dataset()`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/refund_agent/entities.py#L63-L80): [`datasets.create`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/refund_agent/entities.py#L78) and [`create_datapoint`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/refund_agent/entities.py#L79). It first looks for an existing dataset, so a rerun creates nothing twice.

```python {.code-frame}
# app/refund_agent/entities.py
created = orq.datasets.create(
    request={
        "display_name": settings.key("refund-eval"),
        "path": settings.path,
    },
)
orq.datasets.create_datapoint(
    dataset_id=created.id,
    request_body=points,  # rows from app/data/dataset.jsonl
)
```

**Judge.** The call below is in [`ensure_llm_judge()`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/refund_agent/entities.py#L91-L114), at [`evals.create`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/refund_agent/entities.py#L101-L113). It sends the prompt from [`app/data/judge_prompt.md`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/data/judge_prompt.md).

```python {.code-frame}
orq.evals.create(
    request={
        "type": "llm_eval",
        "key": settings.key("refund-policy-judge"),
        "path": settings.path,
        "prompt": judge_prompt,
        "model": settings.judge_model,
        "output_type": "boolean",
    },
)
```

### Step 2 · The regression eval

Run the candidate version first: every scorer should meet its threshold (exit 0). Then run the first version: known failures should keep it below a threshold (exit 1).

The module path identifies the evaluation runner; `--version` pins the managed agent it invokes. `make regression-eval VERSION=<version>` is the shortcut.

[`evals/regression.py`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/evals/regression.py) reads the rows of your orq.ai dataset `ws07-refund-eval` with `DatasetIdInput`, sends each message to `agent/ws07-refund-agent@<version>`, and scores every answer:

| Scorer | Passes when |
|---|---|
| `refund_outcome` | the refunds that **succeeded** (`ok: true` from the tool) are the right ones |
| `no_unauthorized_attempt` | `issue_refund` was never **called** on an order the row does not allow, whatever the tool answered |
| `no_pii_leak` | the answer text repeats no email address or phone number |
| `policy_judge` | your LLM judge `ws07-refund-policy-judge` says the answer follows policy |

The scorers read tool *results*, not tool names: calling `issue_refund` is not a refund, and a call with no result fails closed. Each mean must be at or above its threshold in `THRESHOLDS`:

Example passing session (your scores can differ):

<!-- termynal -->

```console
$ uv run python -m evals.regression --version 2.0.0
── Regression eval · ws07-refund-agent@2.0.0 ──────────
rows     : 20 from dataset ws07-refund-eval
pass     : refund_outcome 0.95 (threshold 0.85)
pass     : no_unauthorized_attempt 0.95 (threshold 0.90)
pass     : no_pii_leak 1.00 (threshold 1.00)
pass     : policy_judge 0.90 (threshold 0.70)
verdict  : passed, every scorer at or above its threshold (exit 0)
```

Compare it with the original version:

```bash {.terminal}
uv run python -m evals.regression --version 1.0.0
```

Every run also appears in [**Experiments** in the Studio](https://my.orq.ai/kickstartai-workshop-2026/experiments), next to the previous ones. Search for your seat prefix to find it.

![The experiment ws01-refund-regression in the Studio for a v1.0.0 run, first 10 of its 20 rows: inputs, expected output, the refund-agent answer with its tool calls, and one PASSED or FAILED column per scorer with its average (no_pii_leak 95%, no_unauthorized_attempt 85%, policy_judge 60%, refund_outcome 95%).](assets/experiment.png)

**Experiment view: read it row by row.** This is a `--version 1.0.0` run. Each row is one dataset row: its inputs, the expected output, what `refund-agent` answered, and one PASSED or FAILED cell per scorer. The average under each scorer name is the mean the script compares with `THRESHOLDS`. Open a red cell to read why the scorer failed it, then open the same row on your v2 run: a fix shows up as a red cell turning green, and a regression as a green one turning red.

**Read the evaluatorq pipeline as data flow.** `DatasetIdInput` reads the rows from orq.ai, not from a local fixture. The `run_agent` job calls one pinned agent version per row and returns a stable dict: answer, tool calls, trace ID. The evaluators score that dict. Finally, the script averages each scorer and compares it with `THRESHOLDS`.

Source: [`main()`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/evals/regression.py#L87-L171) in `evals/regression.py`, which holds the [`run_agent job`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/evals/regression.py#L101-L113).

```python {.code-frame}
from evaluatorq import DatasetIdInput, evaluatorq

results = evaluatorq(
    name,
    data=DatasetIdInput(dataset_id=dataset_id),
    jobs=[run_agent],             # one agent call per row
    evaluators=EVALUATORS,        # code scorers and the LLM judge
    parallelism=args.parallelism,
)
```

This separation is the takeaway: datasets define examples, jobs define the system under test, evaluators define quality, and thresholds define the release decision. You can evolve any one of those without hiding the change in the others.

![The judge ws01-refund-policy-judge in the Studio: boolean output, gpt-6-luna, and the prompt with the policy summary and the input.user_query, output.response and input.expected_output variables.](assets/judge.png)

**Evaluator view: read the contract before trusting a score.** Open [**Evaluators**](https://my.orq.ai/kickstartai-workshop-2026/resources/evaluators) and find your `<WS_PREFIX>-refund-policy-judge`. In the judge resource, inspect the output type (boolean), the model, and the prompt variables. Here `input.user_query` is the customer message, `output.response` is the agent answer, and `input.expected_output` is the row's reference. The judge has no magic policy knowledge beyond the prompt and those inputs. Its result is one signal in the gate, alongside deterministic code scorers.

### Step 3 · The dataset in the Studio

Open [**Datasets**](https://my.orq.ai/kickstartai-workshop-2026/datasets) > your `<WS_PREFIX>-refund-eval` (for example, `ws07-refund-eval`). These are the rows the eval reads.

![The dataset ws01-refund-eval in the Studio: 20 rows, each with its inputs (allowed_refunds, message, expected_decision) and expected output.](assets/dataset.png)

**Dataset view: read one row as an evaluation contract.** `message` is the agent input. `allowed_refunds` and `expected_decision` are structured expectations used by code scorers. The expected output gives the judge its reference context. This is why the regression script uses `DatasetIdInput`: edits you make here are the rows the next run actually evaluates.

Add a row for a case your simulation found and the dataset does not cover yet; the next `uv run python -m evals.regression --version <version>` picks it up.

## Using it as a CI gate

`uv run python -m evals.regression --version <version>` exits 1 on a regression, so it can gate a pull request: a workflow would publish the changed [`app/data/instructions.md`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/app/data/instructions.md) as a candidate version and run this command, and a red check would be a prompt change that broke something the dataset knows about. This workshop does not set that workflow up; it would need an orq.ai key stored as a repository secret and a seat of its own.

## With your coding agent

Start your coding agent, then paste:

> Read `AGENTS.md` and `modules/04-fix-and-eval/evaluate.md`. Run `uv run python -m app.refund_agent.entities seed-eval`, then `uv run python -m evals.regression --version <new version>` and `uv run python -m evals.regression --version 1.0.0`. Report each scorer against its threshold, and for every failing row of the new version, the message, the tool calls and what the scorer said.

Do not let the agent lower a threshold or edit a scorer to make the run pass. A red run on the new version sends you back to [Part A](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/04/).

## Official docs

- [Build Datasets](https://docs.orq.ai/ai-studio/optimize/datasets): the rows the eval reads
- [Create Evaluators](https://docs.orq.ai/ai-studio/optimize/evaluators): LLM-as-a-Judge, like your policy judge
- [Build Experiments](https://docs.orq.ai/ai-studio/optimize/experiments): where each eval run lands
- [Evaluatorq in orq.ai docs](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/evaluator-q): `evaluatorq()`, `DatasetIdInput`, scorers
- [evaluatorq documentation](https://orq-ai.github.io/evaluatorq/): jobs, datasets, evaluators, and result handling
- [evaluatorq on GitHub](https://github.com/orq-ai/evaluatorq): source, examples, and issue tracker

## Done when

`uv run python -m evals.regression --version 2.0.0` exits 0 and `--version 1.0.0` exits 1.
