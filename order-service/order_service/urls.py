from django.urls import include, path

urlpatterns = [
    path("api/orders/", include("orders.urls")),
]
