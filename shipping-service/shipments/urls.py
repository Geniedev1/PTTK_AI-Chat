from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ShipmentViewSet


router = DefaultRouter(trailing_slash=False)
router.register(r"shipments", ShipmentViewSet, basename="shipment")

urlpatterns = [
    path("", include(router.urls)),
]
