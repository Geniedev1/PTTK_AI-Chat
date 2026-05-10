from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    order_id = models.IntegerField(db_index=True)
    customer_id = models.IntegerField(null=True, blank=True, db_index=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    provider = models.CharField(max_length=32, default="mock")
    provider_reference = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    failure_reason = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_id", "status"]),
            models.Index(fields=["customer_id", "status"]),
            models.Index(fields=["session_key", "status"]),
        ]

    def can_transition_to(self, new_status):
        allowed = {
            self.Status.PENDING: {self.Status.PROCESSING, self.Status.PAID, self.Status.FAILED, self.Status.CANCELLED},
            self.Status.PROCESSING: {self.Status.PAID, self.Status.FAILED, self.Status.CANCELLED},
            self.Status.PAID: {self.Status.REFUNDED},
            self.Status.FAILED: set(),
            self.Status.CANCELLED: set(),
            self.Status.REFUNDED: set(),
        }
        return new_status == self.status or new_status in allowed[self.status]

    def __str__(self):
        return f"Payment #{self.pk} order={self.order_id} status={self.status}"


class PaymentMethod(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="method")
    method_type = models.CharField(max_length=32, default="mock")
    provider = models.CharField(max_length=32, default="mock")
    masked_account = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PaymentMethod payment={self.payment_id} type={self.method_type}"


class PaymentTransaction(models.Model):
    class Type(models.TextChoices):
        AUTHORIZE = "AUTHORIZE", "Authorize"
        CAPTURE = "CAPTURE", "Capture"
        FAIL = "FAIL", "Fail"
        CANCEL = "CANCEL", "Cancel"
        REFUND = "REFUND", "Refund"

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    provider_reference = models.CharField(max_length=128, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment", "transaction_type"]),
            models.Index(fields=["provider_reference"]),
        ]

    def __str__(self):
        return f"PaymentTransaction payment={self.payment_id} type={self.transaction_type}"


class PaymentRefund(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="refunds")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, default=Payment.Status.REFUNDED)
    provider_reference = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PaymentRefund payment={self.payment_id} amount={self.amount}"
