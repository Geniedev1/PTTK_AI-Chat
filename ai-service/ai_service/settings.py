import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "ai-service-secret-key")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "*").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "corsheaders",
    "recommendations",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "ai_service.middleware.RequestContextMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "ai_service.urls"
WSGI_APPLICATION = "ai_service.wsgi.application"

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

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = False

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

CORS_ALLOW_ALL_ORIGINS = True

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8004")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8003")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8005")
INTERACTION_SERVICE_URL = os.getenv("INTERACTION_SERVICE_URL", "http://interaction-service:8006")
INTERNAL_ADMIN_KEY = os.getenv("INTERNAL_ADMIN_KEY", "change-this-in-dev")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
RECOMMENDATION_LIMIT_DEFAULT = int(os.getenv("RECOMMENDATION_LIMIT_DEFAULT", "10"))
RECOMMENDATION_LIMIT_MAX = int(os.getenv("RECOMMENDATION_LIMIT_MAX", "20"))
DEEP_MODEL_ENABLED = os.getenv("DEEP_MODEL_ENABLED", "true").lower() == "true"
DEEP_MODEL_ARTIFACT_DIR = Path(
    os.getenv("DEEP_MODEL_ARTIFACT_DIR", BASE_DIR / "artifacts" / "deep_model" / "11b")
)
DEEP_MODEL_SCORE_ALPHA = float(os.getenv("DEEP_MODEL_SCORE_ALPHA", "0.35"))
DEEP_MODEL_SCORE_CLIP_MIN = float(os.getenv("DEEP_MODEL_SCORE_CLIP_MIN", "0.0"))
DEEP_MODEL_SCORE_CLIP_MAX = float(os.getenv("DEEP_MODEL_SCORE_CLIP_MAX", "1.0"))
CHAT_RETRIEVAL_LIMIT = int(os.getenv("CHAT_RETRIEVAL_LIMIT", "5"))
CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", "4"))
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").strip().lower()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-5-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_ENABLE_EMBEDDINGS = os.getenv("OPENAI_ENABLE_EMBEDDINGS", "true").lower() == "true"
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-flash-lite-latest")
KNOWLEDGE_BASE_DIR = Path(os.getenv("KNOWLEDGE_BASE_DIR", BASE_DIR / "knowledge_base"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        }
    },
    "loggers": {
        "ai_service.request": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "recommendations": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
