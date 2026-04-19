from django.core.management.base import BaseCommand
from django.db import transaction

from interactions.knowledge_graph import get_graph_store
from interactions.models import InteractionEvent


class Command(BaseCommand):
    help = "Clear interaction events and optionally clear Neo4j graph data for a clean personalization baseline."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-graph-clear",
            action="store_true",
            help="Only clear interaction events in PostgreSQL and keep existing Neo4j graph data.",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            deleted_events = InteractionEvent.objects.count()
            InteractionEvent.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f"Interaction events cleared: {deleted_events}"))

        if options["skip_graph_clear"]:
            self.stdout.write("Neo4j graph clear skipped by option.")
            return

        graph_store = get_graph_store()
        if not graph_store.enabled:
            self.stdout.write("Neo4j is not configured. Graph clear skipped.")
            return

        result = graph_store.clear_graph()
        self.stdout.write(self.style.SUCCESS(f"Neo4j graph cleared: {result}"))
