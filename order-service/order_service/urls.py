from django.urls import include, path

urlpatterns = [
    path("api/orders", include("orders.urls")),
    path("api/orders/", include("orders.urls")),
]
