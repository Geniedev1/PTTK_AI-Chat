from django.urls import include, path


urlpatterns = [
    path("api/shipping", include("shipments.urls")),
    path("api/shipping/", include("shipments.urls")),
]
