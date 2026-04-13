import uuid

from django.db import models
from django.utils import timezone

from .constants import EVENT_SIGNAL_WEIGHTS, EVENT_TYPE_CHOICES


class InteractionEvent(models.Model):
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_type = models.CharField(max_length=64, choices=EVENT_TYPE_CHOICES)
    user_id = models.IntegerField(null=True, blank=True)
    session_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    product_id = models.IntegerField(null=True, blank=True, db_index=True)
    query_text = models.CharField(max_length=255, null=True, blank=True)
    source = models.CharField(max_length=32, default="backend")
    signal_weight = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(fields=["event_type", "timestamp"]),
            models.Index(fields=["user_id", "timestamp"]),
            models.Index(fields=["product_id", "timestamp"]),
        ]

    def save(self, *args, **kwargs):
        self.signal_weight = EVENT_SIGNAL_WEIGHTS.get(self.event_type, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.event_type} ({self.event_id})"
