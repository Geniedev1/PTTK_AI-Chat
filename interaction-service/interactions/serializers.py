from rest_framework import serializers

from .constants import EVENT_SIGNAL_WEIGHTS
from .models import InteractionEvent


class InteractionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractionEvent
        fields = [
            "id",
            "event_id",
            "event_type",
            "user_id",
            "session_id",
            "product_id",
            "query_text",
            "source",
            "signal_weight",
            "timestamp",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class InteractionEventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractionEvent
        fields = [
            "event_type",
            "user_id",
            "session_id",
            "product_id",
            "query_text",
            "source",
            "timestamp",
            "metadata",
        ]

    def validate(self, attrs):
        if not attrs.get("user_id") and not attrs.get("session_id"):
            raise serializers.ValidationError("Provide user_id or session_id.")

        metadata = attrs.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise serializers.ValidationError("metadata must be an object.")

        event_type = attrs.get("event_type")
        if event_type not in EVENT_SIGNAL_WEIGHTS:
            raise serializers.ValidationError("Unsupported event_type.")

        return attrs
