from rest_framework import serializers

from .models import Order, OrderItem, OrderNote, OrderStatusHistory


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
    status_history = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
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
            "status_history",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_purchase_succeeded(self, obj):
        return obj.purchase_succeeded()

    def get_purchase_event(self, obj):
        return obj.purchase_event()

    def get_status_history(self, obj):
        rows = obj.status_history.all()[:10]
        return OrderStatusHistorySerializer(rows, many=True).data

    def get_notes(self, obj):
        rows = obj.notes.all()[:10]
        return OrderNoteSerializer(rows, many=True).data


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ["id", "old_status", "new_status", "changed_by", "metadata", "created_at"]
        read_only_fields = fields


class OrderNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderNote
        fields = ["id", "note", "created_by", "is_internal", "created_at"]
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    clear_cart = serializers.BooleanField(default=True)


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
