from rest_framework import serializers

from .models import Payment, PaymentMethod, PaymentRefund, PaymentTransaction


class PaymentSerializer(serializers.ModelSerializer):
    method = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()
    refunds = serializers.SerializerMethodField()

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
            "method",
            "transactions",
            "refunds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_method(self, obj):
        try:
            method = obj.method
        except PaymentMethod.DoesNotExist:
            return None
        return PaymentMethodSerializer(method).data

    def get_transactions(self, obj):
        return PaymentTransactionSerializer(obj.transactions.all()[:10], many=True).data

    def get_refunds(self, obj):
        return PaymentRefundSerializer(obj.refunds.all()[:10], many=True).data


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "method_type", "provider", "masked_account", "metadata", "created_at"]
        read_only_fields = fields


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ["id", "transaction_type", "provider_reference", "amount", "status", "metadata", "created_at"]
        read_only_fields = fields


class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = ["id", "amount", "reason", "status", "provider_reference", "created_at"]
        read_only_fields = fields


class PaymentCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    customer_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    session_key = serializers.CharField(required=False, allow_blank=False, max_length=40)
    currency = serializers.CharField(required=False, max_length=3, default="USD")
    provider = serializers.CharField(required=False, max_length=32, default="mock")
    method_type = serializers.CharField(required=False, max_length=32, default="mock")
    masked_account = serializers.CharField(required=False, allow_blank=True, max_length=64)
    idempotency_key = serializers.CharField(required=False, allow_blank=False, max_length=128)

    def validate(self, attrs):
        if attrs.get("customer_id") is None and not attrs.get("session_key"):
            raise serializers.ValidationError("Provide customer_id or session_key.")
        attrs["currency"] = attrs.get("currency", "USD").upper()
        return attrs


class PaymentFailSerializer(serializers.Serializer):
    failure_reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class PaymentRefundRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
