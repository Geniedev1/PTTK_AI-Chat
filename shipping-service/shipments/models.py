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
    delivery_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    carrier = models.CharField(max_length=64, default="mock")
    tracking_number = models.CharField(max_length=64, blank=True, db_index=True)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipper_id = models.IntegerField(null=True, blank=True, db_index=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    distance_km_snapshot = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    assignment_source = models.CharField(max_length=20, blank=True)
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
            models.Index(fields=["shipper_id", "status"]),
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


class ShipmentAddress(models.Model):
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name="delivery_address")
    recipient_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ShipmentAddress shipment={self.shipment_id}"


class ShipmentTrackingEvent(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="tracking_events")
    status = models.CharField(max_length=20)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    event_time = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-event_time"]
        indexes = [
            models.Index(fields=["shipment", "status"]),
            models.Index(fields=["event_time"]),
        ]

    def __str__(self):
        return f"ShipmentTrackingEvent shipment={self.shipment_id} status={self.status}"


class ShippingRate(models.Model):
    carrier = models.CharField(max_length=64)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    base_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_days_min = models.PositiveIntegerField(default=1)
    estimated_days_max = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["carrier", "country", "city"]
        indexes = [
            models.Index(fields=["carrier", "country", "city"]),
        ]

    def __str__(self):
        return f"{self.carrier} {self.country}/{self.city} - {self.base_fee}"


class ShipperProfile(models.Model):
    staff_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    current_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    last_location_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "staff_id"]
        indexes = [
            models.Index(fields=["is_available"]),
            models.Index(fields=["staff_id"]),
        ]

    def __str__(self):
        return f"Shipper {self.name} staff={self.staff_id}"
