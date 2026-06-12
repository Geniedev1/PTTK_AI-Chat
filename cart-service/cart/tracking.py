import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 0.5


def emit_interaction_event(*, event_type, session_id=None, user_id=None, product_id=None, query_text=None, source="backend", metadata=None):
    interaction_service_url = getattr(settings, "INTERACTION_SERVICE_URL", "")
    if not interaction_service_url or (not session_id and not user_id):
        return False

    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "session_id": session_id,
        "product_id": product_id,
        "query_text": query_text,
        "source": source,
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
