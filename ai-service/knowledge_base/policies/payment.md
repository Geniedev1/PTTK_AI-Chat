# Payment Policy

Orders are considered paid only after the payment confirmation step is recorded by the order workflow.
Supported payment methods may include cash on delivery, bank transfer, or online payment depending on the store setup.
If payment fails, the order should remain pending or be cancelled instead of being treated as completed.

Current payment status must always be checked from the order service rather than from static knowledge.
