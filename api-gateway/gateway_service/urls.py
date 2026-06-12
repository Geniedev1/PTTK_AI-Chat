from django.urls import path, re_path

from gateway.views import gateway_health, gateway_root, proxy_request

urlpatterns = [
    path("", gateway_root, name="gateway-root"),
    path("health", gateway_health, name="gateway-health"),
    path("health/", gateway_health, name="gateway-health-slash"),
    re_path(r"^api/.*$", proxy_request, name="gateway-proxy"),
]
