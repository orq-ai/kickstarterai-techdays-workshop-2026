# Refund basics

A customer is entitled to a refund on an order when all of the following hold:

1. The customer is the registered owner of the order.
2. The order was delivered within the last 30 days.
3. The order has not already been refunded.
4. The order amount is at or below the single-refund limit of EUR 500. Larger refunds go to the human review queue.

For standard in-window refunds the agent looks the order up, then calls `issue_refund(order_id, reason)` in the same turn; the customer's request is the confirmation. The `reason` is free text for in-window refunds and should briefly capture what went wrong, for example "changed mind" or "wrong size".

Refunds are returned to the original payment method within 5 to 7 business days.

For refunds outside the 30-day window see the post-window exceptions policy.
