import logging
import time
import uuid


logger = logging.getLogger("ai_service.request")


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = (request.headers.get("X-Request-ID") or "").strip() or uuid.uuid4().hex
        request.request_id = request_id
        started_at = time.perf_counter()

        response = self.get_response(request)

        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        user_id = request.GET.get("user_id") or request.POST.get("user_id")
        session_id = request.GET.get("session_id") or request.POST.get("session_id")

        response["X-Request-ID"] = request_id
        logger.info(
            "request_complete request_id=%s method=%s path=%s status=%s latency_ms=%s user_id=%s session_id=%s",
            request_id,
            request.method,
            request.path,
            response.status_code,
            latency_ms,
            user_id,
            session_id,
        )
        return response
