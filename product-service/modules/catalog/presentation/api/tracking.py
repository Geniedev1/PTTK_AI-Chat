import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 0.5


def _get_session_id(request):
    return (request.headers.get("X-Interaction-Session-Key") or request.headers.get("X-Cart-Session-Key") or "").strip()[:64]


def _get_user_id(request):
    value = request.query_params.get("customer_id") or request.headers.get("X-Customer-Id") or request.headers.get("X-User-Id")
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _get_source(request):
    return request.query_params.get("source") or request.headers.get("X-Interaction-Source") or "backend"


def emit_request_event(request, *, event_type, product_id=None, query_text=None, metadata=None):
    interaction_service_url = getattr(settings, "INTERACTION_SERVICE_URL", "")
    session_id = _get_session_id(request)
    user_id = _get_user_id(request)
    if not interaction_service_url or (not session_id and not user_id):
        return False

    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "session_id": session_id,
        "product_id": product_id,
        "query_text": query_text,
        "source": _get_source(request),
        "metadata": metadata or {},
    }

    try:
        response = requests.post(
            f"{interaction_service_url}/api/interactions/events",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return response.status_code == 201
    except requests.RequestException as exc:
        logger.warning("Failed to emit interaction event %s: %s", event_type, exc)
        return False
