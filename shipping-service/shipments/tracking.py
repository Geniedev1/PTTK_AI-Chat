import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 0.5


def emit_interaction_event(*, event_type, shipment, metadata=None):
    interaction_service_url = getattr(settings, "INTERACTION_SERVICE_URL", "")
    if not interaction_service_url or (not shipment.session_key and shipment.customer_id is None):
        return False

    payload = {
        "event_type": event_type,
        "user_id": shipment.customer_id,
        "session_id": shipment.session_key,
        "source": "shipping-service",
        "metadata": {
            "shipment_id": shipment.id,
            "order_id": shipment.order_id,
            "carrier": shipment.carrier,
            "tracking_number": shipment.tracking_number,
            "status": shipment.status,
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
        logger.warning("Failed to emit shipment event %s: %s", event_type, exc)
        return False
