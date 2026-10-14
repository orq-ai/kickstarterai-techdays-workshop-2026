# Business case

Lumen Goods needs a customer-service agent that can decide which refund requests are safe to handle automatically and which need a person.

## Lumen Goods and its customers

Lumen Goods sells home and tech accessories across the EU and UK. Customers are already signed in when they ask for help, so the business can associate a request with the customer’s orders without asking the customer to provide an account identifier.

The business goal is not to refund everything. It is to give eligible customers a quick, consistent outcome while preserving a clear path to human support for requests that need more evidence or judgment.

## Scope

The agent handles refund requests only.

| In scope | Handled by human support |
|---|---|
| Order lookup and refund eligibility | Shipping-status questions |
| Standard in-window refunds | Billing disputes and chargebacks |
| Evidence-backed post-window exceptions | Account changes |
| Explaining a refund outcome | Product advice and compatibility |

This boundary keeps the decision small enough to test: can this specific order be refunded automatically, and if not, what should happen next?

## Policy requirements

| Check | Required outcome |
|---|---|
| Order belongs to the signed-in customer | Continue |
| Delivered within 30 days | Refund for any reason |
| Already refunded | Refuse |
| Above EUR 500 | Route to human review |
| Outside 30 days | Require one listed exception and supporting evidence |

The listed post-window exceptions are damaged in transit, never received, and defective on arrival. Each needs evidence appropriate to the claim. If the available information cannot establish the right path, the request goes to human support rather than becoming a new automatic rule.

![A refund request is checked for ownership, prior refund state, amount, and delivery window; it is automatically refunded when eligible, refused for failed order checks, or routed to human review when evidence or limit rules require it.](assets/refund-policy-flow.png)

## Business acceptance criteria

A solution for this business case must demonstrate the following outcomes:

| Situation | Expected outcome |
|---|---|
| Eligible in-window order | Refund succeeds and the customer receives a clear confirmation. |
| Order that is not available to the signed-in customer | No order information is disclosed. |
| Already-refunded order | No second refund is issued. |
| Order above the automatic limit | The request is routed to human review. |
| Post-window request without sufficient evidence | The request is not automatically refunded. |
| Request outside refund scope | The customer is directed to the appropriate human-support path. |

The [Solution design](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-solution-design/) page shows the v1 approach that turns these requirements into a managed agent.
