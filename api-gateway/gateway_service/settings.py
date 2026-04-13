import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-gateway-secret-key")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "*").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "gateway",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "gateway.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "gateway_service.urls"
WSGI_APPLICATION = "gateway_service.wsgi.application"
ASGI_APPLICATION = "gateway_service.asgi.application"

TEMPLATES = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = False

SERVICE_ROUTES = {
    "/api/staff/": os.getenv("STAFF_SERVICE_URL", "http://staff-service:8001"),
    "/api/customers/": os.getenv("CUSTOMER_SERVICE_URL", "http://customer-service:8002"),
    "/api/cart/": os.getenv("CART_SERVICE_URL", "http://cart-service:8003"),
    "/api/products/": os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8004"),
    "/api/orders/": os.getenv("ORDER_SERVICE_URL", "http://order-service:8005"),
    "/api/interactions/": os.getenv("INTERACTION_SERVICE_URL", "http://interaction-service:8006"),
}

PROXY_TIMEOUT = int(os.getenv("PROXY_TIMEOUT", "30"))
