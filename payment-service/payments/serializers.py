from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order_id",
            "customer_id",
            "session_key",
            "amount",
            "currency",
            "provider",
            "provider_reference",
            "status",
            "failure_reason",
            "idempotency_key",
            "paid_at",
            "failed_at",
            "cancelled_at",
            "refunded_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PaymentCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    customer_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    session_key = serializers.CharField(required=False, allow_blank=False, max_length=40)
    currency = serializers.CharField(required=False, max_length=3, default="USD")
    provider = serializers.CharField(required=False, max_length=32, default="mock")
    idempotency_key = serializers.CharField(required=False, allow_blank=False, max_length=128)

    def validate(self, attrs):
        if attrs.get("customer_id") is None and not attrs.get("session_key"):
            raise serializers.ValidationError("Provide customer_id or session_key.")
        attrs["currency"] = attrs.get("currency", "USD").upper()
        return attrs


class PaymentFailSerializer(serializers.Serializer):
    failure_reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
