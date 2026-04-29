from django.db import models


class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        READY_TO_SHIP = "READY_TO_SHIP", "Ready to ship"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    order_id = models.IntegerField(unique=True)
    customer_id = models.IntegerField(null=True, blank=True, db_index=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    recipient_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=64, default="mock")
    tracking_number = models.CharField(max_length=64, blank=True, db_index=True)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    failure_reason = models.TextField(blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer_id", "status"]),
            models.Index(fields=["session_key", "status"]),
        ]

    def can_transition_to(self, new_status):
        allowed = {
            self.Status.PENDING: {self.Status.READY_TO_SHIP, self.Status.SHIPPED, self.Status.CANCELLED, self.Status.FAILED},
            self.Status.READY_TO_SHIP: {self.Status.SHIPPED, self.Status.CANCELLED, self.Status.FAILED},
            self.Status.SHIPPED: {self.Status.DELIVERED, self.Status.FAILED},
            self.Status.DELIVERED: set(),
            self.Status.FAILED: set(),
            self.Status.CANCELLED: set(),
        }
        return new_status == self.status or new_status in allowed[self.status]

    def __str__(self):
        return f"Shipment #{self.pk} order={self.order_id} status={self.status}"
