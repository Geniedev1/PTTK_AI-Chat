import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
}


def gateway_root(request):
    return HttpResponse("API Gateway is running\n", content_type="text/plain")


def gateway_health(request):
    return HttpResponse("Gateway is running\n", content_type="text/plain")


def _resolve_backend_base(path):
    for prefix, base_url in settings.SERVICE_ROUTES.items():
        if path.startswith(prefix):
            return base_url.rstrip("/")
    return None


def _build_forward_headers(request):
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    remote_addr = request.META.get("REMOTE_ADDR")
    if forwarded_for and remote_addr:
        headers["X-Forwarded-For"] = f"{forwarded_for}, {remote_addr}"
    elif remote_addr:
        headers["X-Forwarded-For"] = remote_addr

    if remote_addr:
        headers["X-Real-IP"] = remote_addr

    headers["X-Forwarded-Proto"] = "https" if request.is_secure() else "http"
    return headers


@csrf_exempt
def proxy_request(request):
    backend_base = _resolve_backend_base(request.path)
    if not backend_base:
        return JsonResponse({"detail": "No upstream service matched this path."}, status=404)

    target_url = f"{backend_base}{request.get_full_path()}"
    request_body = request.body if request.body else None

    try:
        upstream_response = requests.request(
            method=request.method,
            url=target_url,
            headers=_build_forward_headers(request),
            data=request_body,
            cookies=request.COOKIES,
            allow_redirects=False,
            timeout=settings.PROXY_TIMEOUT,
        )
    except requests.RequestException as exc:
        return JsonResponse(
            {"detail": "Bad gateway", "upstream": target_url, "error": str(exc)},
            status=502,
        )

    response = HttpResponse(
        upstream_response.content,
        status=upstream_response.status_code,
    )

    for key, value in upstream_response.headers.items():
        if key.lower() in HOP_BY_HOP_HEADERS or key.lower() == "content-length":
            continue
        response[key] = value

    return response
