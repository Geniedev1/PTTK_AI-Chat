from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_id",
            "product_name_snapshot",
            "price_snapshot",
            "quantity",
            "created_at",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    purchase_succeeded = serializers.SerializerMethodField()
    purchase_event = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_id",
            "session_key",
            "status",
            "total_amount",
            "purchase_succeeded",
            "purchase_event",
            "confirmed_at",
            "paid_at",
            "completed_at",
            "cancelled_at",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_purchase_succeeded(self, obj):
        return obj.purchase_succeeded()

    def get_purchase_event(self, obj):
        return obj.purchase_event()


class OrderCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    clear_cart = serializers.BooleanField(default=True)


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
