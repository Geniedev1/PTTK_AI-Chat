from decimal import Decimal

from rest_framework import serializers


class VariantSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    sku = serializers.CharField()
    name = serializers.CharField()
    attributes = serializers.JSONField(required=False)
    stock = serializers.IntegerField(min_value=0)
    price_override = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal("0.00"),
    )
    is_default = serializers.BooleanField(required=False)

    def validate_attributes(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("attributes must be a JSON object.")
        return value


class ProductWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(required=False, allow_blank=True)
    short_description = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    full_description = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    brand_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    product_type_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))
    stock = serializers.IntegerField(min_value=0, required=False, default=0)
    attributes = serializers.JSONField(required=False)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)
    image_urls = serializers.ListField(child=serializers.URLField(), required=False)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_attributes(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("attributes must be a JSON object.")
        return value

    def validate_tags(self, value):
        return [item.strip() for item in value if item and item.strip()]

    def validate(self, attrs):
        description = attrs.get("description", "")
        full_description = attrs.get("full_description", "")

        if full_description and not description:
            attrs["description"] = full_description
        elif description and not full_description:
            attrs["full_description"] = description
        elif not full_description and not description:
            attrs["description"] = ""
            attrs["full_description"] = ""

        attrs.setdefault("slug", "")
        attrs.setdefault("short_description", "")
        attrs.setdefault("tags", [])
        attrs.setdefault("image_urls", [])
        attrs.pop("full_description", None)
        return attrs


class ProductReadSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    short_description = serializers.CharField()
    description = serializers.CharField()
    full_description = serializers.CharField()
    category_id = serializers.IntegerField(allow_null=True)
    brand_id = serializers.IntegerField(allow_null=True)
    product_type_id = serializers.IntegerField(allow_null=True)
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock = serializers.IntegerField()
    attributes = serializers.JSONField()
    is_active = serializers.BooleanField()
    status = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    image_urls = serializers.ListField(child=serializers.URLField())
    has_stock = serializers.BooleanField()
    variants = VariantSerializer(many=True)
