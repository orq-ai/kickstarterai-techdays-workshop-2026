---
marp: true
theme: orq
paginate: true
---

# Is your agent behaving like you expect?

KickstartAI TechDays · 15 October 2026

90-minute session · module checkpoints follow the course pages

![w:220](assets/kickstart-qr.png)

---

## Onboarding

orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/00/

---

## Coding agents · optional

orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/01/

---

## Refund agent

Understand the requirements, then inspect your managed agent and its hosted tools.

Foundations → Use Case → Agent Design → Build the Agent

orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02/

First-hour checkpoint: gateway request, hello agent, and a Python refund-agent client that prints tool results and a trace ID.

---

## Simulation

Two personas × three scenarios. Run v1 twice.

After every agent reply, the judge audits the accumulated transcript, including tool evidence, and directs the simulator to continue or stop. Find at least two behaviours you would not ship, with supporting conversations; inspect incomplete results and save the baseline report.

orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/03/

---

## Fix and replay

Edit instructions → publish v2 → compare versions → replay the saved baseline twice.

Keep the ordinary refund working; investigate every UNKNOWN result.

orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/04/

---

## Prove it with an eval

Create the dataset and policy judge with `make seed-eval`.

Run `make regression-eval VERSION=2.0.0`, then compare with `VERSION=1.0.0`.

Every scorer's mean must meet its threshold. Use the exit code as a release gate.

orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/04-evaluate/

---

## Take home

Add each new failure to your dataset. Rerun the gate on every change.

Connect the evaluation command to CI as a next step.

github.com/orq-ai/kickstarterai-techdays-workshop-2026
