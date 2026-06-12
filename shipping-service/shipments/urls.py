from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ShipmentViewSet, ShipperProfileViewSet


router = DefaultRouter(trailing_slash=False)
router.register(r"shipments", ShipmentViewSet, basename="shipment")
router.register(r"shippers", ShipperProfileViewSet, basename="shipper")

urlpatterns = [
    path("", include(router.urls)),
]
