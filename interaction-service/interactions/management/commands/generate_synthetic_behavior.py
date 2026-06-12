import random
from collections import Counter
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from interactions.constants import EVENT_SIGNAL_WEIGHTS
from interactions.knowledge_graph import ProductCatalogClient
from interactions.models import InteractionEvent


SEARCH_QUERIES = [
    "wireless mouse",
    "gaming keyboard",
    "office chair",
    "ergonomic desk",
    "monitor 27 inch",
    "noise cancelling headset",
    "mechanical keyboard",
    "usb c hub",
    "laptop stand",
    "webcam full hd",
]

CHAT_PROMPTS = [
    "Tu van cho toi mot san pham phu hop nhu cau",
    "San pham nay co uu diem gi",
    "Nen chon mau nao cho cong viec van phong",
    "Co goi y san pham thay the khong",
]


class Command(BaseCommand):
    help = "Generate synthetic behavior events for 100 users with 10+ event types."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=100, help="Number of synthetic users.")
        parser.add_argument("--sessions-per-user", type=int, default=3, help="Sessions generated per user.")
        parser.add_argument("--user-id-start", type=int, default=1, help="Starting user_id value.")
        parser.add_argument("--lookback-days", type=int, default=30, help="Spread timestamps across recent N days.")
        parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible output.")
        parser.add_argument("--source", default="synthetic", help="Source value to tag generated events.")
        parser.add_argument(
            "--clear-source",
            action="store_true",
            help="Delete existing events with the same source before generating new ones.",
        )

    def handle(self, *args, **options):
        users = int(options["users"])
        sessions_per_user = int(options["sessions_per_user"])
        user_id_start = int(options["user_id_start"])
        lookback_days = int(options["lookback_days"])
        seed = int(options["seed"])
        source = str(options["source"]).strip() or "synthetic"
        clear_source = bool(options["clear_source"])

        if users <= 0:
            raise CommandError("--users must be > 0")
        if sessions_per_user <= 0:
            raise CommandError("--sessions-per-user must be > 0")
        if lookback_days <= 0:
            raise CommandError("--lookback-days must be > 0")

        rng = random.Random(seed)
        product_ids, category_lookup = self._load_product_context(rng)
        now = timezone.now()

        events_to_create = []
        event_counts = Counter()
        user_ids = []

        for index in range(users):
            user_id = user_id_start + index
            user_ids.append(user_id)
            for session_index in range(1, sessions_per_user + 1):
                session_id = f"sim-u{user_id}-s{session_index}"
                session_start = now - timedelta(
                    days=rng.randint(0, lookback_days - 1),
                    minutes=rng.randint(0, 23 * 60),
                    seconds=rng.randint(0, 59),
                )
                session_events = self._build_session_events(
                    rng=rng,
                    user_id=user_id,
                    session_id=session_id,
                    session_start=session_start,
                    source=source,
                    product_ids=product_ids,
                    category_lookup=category_lookup,
                )
                events_to_create.extend(session_events)
                for event in session_events:
                    event_counts[event.event_type] += 1

        distinct_event_types = sorted(event_counts.keys())
        if len(distinct_event_types) < 10:
            raise CommandError(
                "Synthetic generation produced fewer than 10 event types. "
                f"Got {len(distinct_event_types)}: {distinct_event_types}"
            )

        with transaction.atomic():
            deleted_rows = 0
            if clear_source:
                deleted_rows = InteractionEvent.objects.filter(source=source).count()
                InteractionEvent.objects.filter(source=source).delete()

            InteractionEvent.objects.bulk_create(events_to_create, batch_size=1000)

        self.stdout.write(self.style.SUCCESS("Synthetic behavior generation completed."))
        self.stdout.write(f"source={source}")
        self.stdout.write(f"users={len(user_ids)} sessions_per_user={sessions_per_user}")
        self.stdout.write(f"events_created={len(events_to_create)}")
        if clear_source:
            self.stdout.write(f"events_deleted_for_source={deleted_rows}")
        self.stdout.write(f"distinct_event_types={len(distinct_event_types)} -> {', '.join(distinct_event_types)}")

    def _load_product_context(self, rng):
        catalog = ProductCatalogClient()
        try:
            products = catalog.fetch_products()
        except Exception:
            products = []

        active_products = [row for row in products if row.get("is_active", False)]
        if active_products:
            product_ids = [int(row["id"]) for row in active_products if row.get("id") is not None]
            category_lookup = {
                int(row["id"]): row.get("category_id")
                for row in active_products
                if row.get("id") is not None
            }
            if product_ids:
                return product_ids, category_lookup

        # Fallback when product-service is unavailable.
        product_ids = list(range(1, 31))
        rng.shuffle(product_ids)
        category_lookup = {product_id: (product_id % 8) + 1 for product_id in product_ids}
        return product_ids, category_lookup

    def _build_session_events(self, *, rng, user_id, session_id, session_start, source, product_ids, category_lookup):
        events = []
        timestamp_cursor = session_start

        def append_event(event_type, *, product_id=None, query_text="", metadata=None):
            nonlocal timestamp_cursor
            timestamp_cursor += timedelta(seconds=rng.randint(20, 180))
            payload = dict(metadata or {})
            if product_id is not None:
                category_id = category_lookup.get(int(product_id))
                if category_id is not None:
                    payload.setdefault("category_id", int(category_id))

            events.append(
                InteractionEvent(
                    event_type=event_type,
                    user_id=user_id,
                    session_id=session_id,
                    product_id=product_id,
                    query_text=query_text,
                    source=source,
                    signal_weight=EVENT_SIGNAL_WEIGHTS.get(event_type, 0),
                    timestamp=timestamp_cursor,
                    metadata=payload,
                )
            )

        append_event("chat_started", query_text="start session", metadata={"channel": "web"})

        journeys = rng.randint(1, 3)
        for _ in range(journeys):
            product_id = int(rng.choice(product_ids))
            query = rng.choice(SEARCH_QUERIES)

            append_event("search_performed", query_text=query, metadata={"search_query": query})
            append_event("product_clicked", product_id=product_id)
            append_event("product_viewed", product_id=product_id)

            if rng.random() < 0.8:
                append_event("cart_viewed", query_text="open cart")
                append_event("cart_item_added", product_id=product_id)

                if rng.random() < 0.6:
                    append_event(
                        "cart_item_quantity_updated",
                        product_id=product_id,
                        metadata={"quantity": rng.randint(2, 4)},
                    )

                if rng.random() < 0.25:
                    append_event("cart_item_removed", product_id=product_id)

                append_event("checkout_started", query_text="checkout")
                append_event("order_created", product_id=product_id)

                if rng.random() < 0.85:
                    append_event("order_paid", product_id=product_id)
                    append_event("order_completed", product_id=product_id)
                else:
                    append_event("order_cancelled", product_id=product_id)

            if rng.random() < 0.75:
                append_event(
                    "chat_message_sent",
                    product_id=product_id,
                    query_text=rng.choice(CHAT_PROMPTS),
                    metadata={"intent": "advice"},
                )

        # Ensure at least one chat message in each session.
        if not any(event.event_type == "chat_message_sent" for event in events):
            append_event(
                "chat_message_sent",
                query_text=rng.choice(CHAT_PROMPTS),
                metadata={"intent": "followup"},
            )

        return events