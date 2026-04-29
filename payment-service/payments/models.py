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
