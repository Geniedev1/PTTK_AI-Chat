from rest_framework import serializers


class VariantSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    sku = serializers.CharField()
    name = serializers.CharField()
    attributes = serializers.JSONField(required=False)
    stock = serializers.IntegerField(min_value=0)
    price_override = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    is_default = serializers.BooleanField(required=False)


class ProductWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    brand_id = serializers.IntegerField(required=False, allow_null=True)
    product_type_id = serializers.IntegerField(required=False, allow_null=True)
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock = serializers.IntegerField(min_value=0, required=False, default=0)
    attributes = serializers.JSONField(required=False)
    is_active = serializers.BooleanField(required=False, default=True)


class ProductReadSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    category_id = serializers.IntegerField(allow_null=True)
    brand_id = serializers.IntegerField(allow_null=True)
    product_type_id = serializers.IntegerField(allow_null=True)
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock = serializers.IntegerField()
    attributes = serializers.JSONField()
    is_active = serializers.BooleanField()
    variants = VariantSerializer(many=True)
