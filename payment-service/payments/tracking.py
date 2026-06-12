import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 0.5


def emit_interaction_event(*, event_type, payment, metadata=None):
    interaction_service_url = getattr(settings, "INTERACTION_SERVICE_URL", "")
    if not interaction_service_url or (not payment.session_key and payment.customer_id is None):
        return False

    payload = {
        "event_type": event_type,
        "user_id": payment.customer_id,
        "session_id": payment.session_key,
        "source": "payment-service",
        "metadata": {
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "status": payment.status,
            **(metadata or {}),
        },
    }

    try:
        response = requests.post(
            f"{interaction_service_url}/api/interactions/events",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return response.status_code == 201
    except requests.RequestException as exc:
        logger.warning("Failed to emit payment event %s: %s", event_type, exc)
        return False
