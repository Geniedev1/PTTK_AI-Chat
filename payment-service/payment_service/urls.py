from django.urls import include, path


urlpatterns = [
    path("api/payments", include("payments.urls")),
    path("api/payments/", include("payments.urls")),
]
