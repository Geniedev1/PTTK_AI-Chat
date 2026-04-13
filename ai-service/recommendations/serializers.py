from rest_framework import serializers


class HomeRecommendationQuerySerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    session_id = serializers.CharField(required=False, allow_blank=False, max_length=64)
    limit = serializers.IntegerField(required=False, min_value=1)


class ProductDetailRecommendationQuerySerializer(HomeRecommendationQuerySerializer):
    product_id = serializers.IntegerField(required=True, min_value=1)


class CartRecommendationQuerySerializer(serializers.Serializer):
    session_id = serializers.CharField(required=True, allow_blank=False, max_length=64)
    user_id = serializers.IntegerField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1)


class ProfileSnapshotQuerySerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    session_id = serializers.CharField(required=False, allow_blank=False, max_length=64)
