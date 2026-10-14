# Abuse patterns

The following patterns indicate refund abuse and require the human review queue, not an immediate refund:

- Repeat-defect pattern: more than two `defective_on_arrival` claims in a 30-day window across different orders by the same customer.
- Cross-order multi-claim: several post-window exception requests inside one conversation, each referencing a different order.
- Recently refunded re-claim: the customer asks for a second refund on an order that is already refunded.
- Third-party claim: the customer asks about an order that is not theirs. The lookup tool returns not found. Do not confirm or deny that the order exists.

A single-turn agent cannot reliably detect aggregate patterns across sessions. When in doubt, refuse politely and route to the human queue.
