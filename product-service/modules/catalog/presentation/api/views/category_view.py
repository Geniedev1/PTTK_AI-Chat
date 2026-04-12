from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from ....infrastructure.models import CategoryModel
from ..serializers.category_serializer import CategorySerializer


class CategoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = CategoryModel.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
