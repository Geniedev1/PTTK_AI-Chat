from django.http import HttpResponse
from django.conf import settings


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _resolve_origin(self, request):
        origin = request.headers.get("Origin")
        if not origin:
            return "*"

        allowed = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        if "*" in allowed or origin in allowed:
            return origin

        return "null"

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        response["Access-Control-Allow-Origin"] = self._resolve_origin(request)
        response["Vary"] = "Origin"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = (
            "Accept,Authorization,Cache-Control,Content-Type,DNT,If-Modified-Since,"
            "Keep-Alive,Origin,User-Agent,X-Requested-With,X-Request-ID,"
            "X-Cart-Session-Key,X-Internal-Admin-Key"
        )
        response["Access-Control-Expose-Headers"] = "X-Request-ID,X-Cart-Session-Key"
        response["Access-Control-Max-Age"] = "86400"
        return response
