from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, allow_blank=False, max_length=4000)
    user_id = serializers.IntegerField(required=False)
    session_id = serializers.CharField(required=False, allow_blank=False, max_length=64)
    customer_id = serializers.IntegerField(required=False)
    product_id = serializers.IntegerField(required=False)
    order_id = serializers.IntegerField(required=False)


class ChatRetrieveRequestSerializer(ChatRequestSerializer):
    limit = serializers.IntegerField(required=False, min_value=1)
