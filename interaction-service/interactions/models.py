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


class BehaviorProfile(models.Model):
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    profile_json = models.JSONField(default=dict, blank=True)
    event_count = models.PositiveIntegerField(default=0)
    last_event_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user_id", "session_id"]),
        ]

    def __str__(self):
        return f"BehaviorProfile user={self.user_id} session={self.session_id}"


class SearchQueryLog(models.Model):
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    query_text = models.CharField(max_length=255)
    result_count = models.PositiveIntegerField(default=0)
    product_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["query_text"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.query_text


class EventAggregate(models.Model):
    metric_name = models.CharField(max_length=100)
    metric_date = models.DateField()
    dimension = models.CharField(max_length=100, blank=True)
    metric_value = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-metric_date", "metric_name"]
        constraints = [
            models.UniqueConstraint(fields=["metric_name", "metric_date", "dimension"], name="unique_event_aggregate_dimension"),
        ]

    def __str__(self):
        return f"{self.metric_name} {self.metric_date} {self.dimension}"
