from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.category_view import CategoryViewSet
from .views.product_view import ProductViewSet


router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]
