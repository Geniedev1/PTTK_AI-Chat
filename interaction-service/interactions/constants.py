EVENT_SIGNAL_WEIGHTS = {
    "search_performed": 1,
    "product_clicked": 2,
    "product_viewed": 1,
    "cart_viewed": 1,
    "cart_item_added": 4,
    "cart_item_removed": 1,
    "cart_item_quantity_updated": 3,
    "checkout_started": 4,
    "order_created": 5,
    "order_paid": 6,
    "order_cancelled": -2,
    "order_completed": 6,
    "payment_started": 3,
    "payment_paid": 6,
    "payment_failed": -2,
    "payment_cancelled": -1,
    "payment_refunded": -3,
    "shipment_created": 2,
    "shipment_ready": 2,
    "shipment_shipped": 3,
    "shipment_delivered": 4,
    "shipment_failed": -2,
    "shipment_cancelled": -1,
    "chat_started": 1,
    "chat_message_sent": 2,
}

EVENT_TYPE_CHOICES = [(event_type, event_type) for event_type in EVENT_SIGNAL_WEIGHTS]

PRODUCT_DISCOVERY_EVENTS = {"search_performed", "product_clicked", "product_viewed"}
PRODUCT_INTEREST_EVENTS = {"product_viewed", "product_clicked", "cart_item_added", "order_paid", "order_completed"}
CART_EVENT_TYPES = {"cart_viewed", "cart_item_added", "cart_item_removed", "cart_item_quantity_updated", "checkout_started"}
