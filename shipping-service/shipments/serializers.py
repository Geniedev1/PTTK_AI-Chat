from rest_framework import serializers

from .models import Shipment, ShipmentAddress, ShipmentTrackingEvent, ShippingRate


class ShipmentSerializer(serializers.ModelSerializer):
    delivery_address = serializers.SerializerMethodField()
    tracking_events = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = [
            "id",
            "order_id",
            "customer_id",
            "session_key",
            "recipient_name",
            "phone",
            "address",
            "city",
            "country",
            "carrier",
            "tracking_number",
            "shipping_fee",
            "status",
            "failure_reason",
            "shipped_at",
            "delivered_at",
            "cancelled_at",
            "delivery_address",
            "tracking_events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_delivery_address(self, obj):
        try:
            address = obj.delivery_address
        except ShipmentAddress.DoesNotExist:
            return None
        return ShipmentAddressSerializer(address).data

    def get_tracking_events(self, obj):
        return ShipmentTrackingEventSerializer(obj.tracking_events.all()[:10], many=True).data


class ShipmentAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentAddress
        fields = ["id", "recipient_name", "phone", "address", "city", "country", "created_at"]
        read_only_fields = fields


class ShipmentTrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentTrackingEvent
        fields = ["id", "status", "location", "description", "event_time", "metadata"]
        read_only_fields = fields


class ShippingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingRate
        fields = ["id", "carrier", "city", "country", "base_fee", "estimated_days_min", "estimated_days_max", "is_active"]
        read_only_fields = fields


class ShipmentCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    customer_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    session_key = serializers.CharField(required=False, allow_blank=False, max_length=40)
    recipient_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=32)
    address = serializers.CharField()
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    country = serializers.CharField(required=False, allow_blank=True, max_length=100)
    carrier = serializers.CharField(required=False, allow_blank=False, max_length=64, default="mock")
    shipping_fee = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, default="0.00")

    def validate(self, attrs):
        if attrs.get("customer_id") is None and not attrs.get("session_key"):
            raise serializers.ValidationError("Provide customer_id or session_key.")
        return attrs


class ShipmentFailSerializer(serializers.Serializer):
    failure_reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
