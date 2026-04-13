from django.core.management.base import BaseCommand, CommandError

from interactions.knowledge_graph import ProductCatalogClient, get_graph_store
from interactions.models import InteractionEvent


class Command(BaseCommand):
    help = "Rebuild the Neo4j knowledge graph from product-service catalog and interaction events."

    def handle(self, *args, **options):
        store = get_graph_store()
        if not store.enabled:
            raise CommandError("Neo4j is not configured. Set NEO4J_URI, NEO4J_USER and NEO4J_PASSWORD first.")

        catalog_client = ProductCatalogClient()
        try:
            categories = catalog_client.fetch_categories()
            products = catalog_client.fetch_products()
        except Exception as exc:
            raise CommandError(f"Failed to fetch product catalog: {exc}") from exc

        interactions = [
            {
                "event_type": event.event_type,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "product_id": event.product_id,
                "query_text": event.query_text,
                "signal_weight": event.signal_weight,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata or {},
            }
            for event in InteractionEvent.objects.all().order_by("timestamp", "id")
        ]
        result = store.rebuild_graph(products, categories, interactions)
        self.stdout.write(self.style.SUCCESS(f"Knowledge graph rebuilt: {result}"))
