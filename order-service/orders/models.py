from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    customer_id = models.IntegerField(null=True, blank=True)
    session_key = models.CharField(max_length=40, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"

    def can_transition_to(self, new_status):
        allowed_transitions = {
            self.Status.PENDING: {self.Status.CONFIRMED, self.Status.PAID, self.Status.CANCELLED},
            self.Status.CONFIRMED: {self.Status.PAID, self.Status.CANCELLED},
            self.Status.PAID: {self.Status.COMPLETED},
            self.Status.CANCELLED: set(),
            self.Status.COMPLETED: set(),
        }
        return new_status == self.status or new_status in allowed_transitions[self.status]

    def purchase_succeeded(self):
        return self.status in {self.Status.PAID, self.Status.COMPLETED}

    def purchase_event(self):
        if self.status == self.Status.COMPLETED:
            return "order_completed"
        if self.status == self.Status.PAID:
            return "order_paid"
        return None


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.IntegerField()
    product_name_snapshot = models.CharField(max_length=255)
    price_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OrderItem order={self.order_id} product={self.product_id}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.CharField(max_length=100, default="system")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "new_status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"OrderStatusHistory order={self.order_id} {self.old_status}->{self.new_status}"


class OrderNote(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notes")
    note = models.TextField()
    created_by = models.CharField(max_length=100, default="system")
    is_internal = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OrderNote order={self.order_id}"
