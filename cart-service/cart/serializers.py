from rest_framework import serializers
from .models import Cart, CartSession

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'customer_id', 'product_id', 'quantity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class CartAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)

class CartUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

class CartSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartSession
        fields = ['id', 'session_key', 'customer_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
