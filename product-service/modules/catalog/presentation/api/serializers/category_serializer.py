from rest_framework import serializers

from ....infrastructure.models import CategoryModel


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ["id", "name", "slug", "parent"]
