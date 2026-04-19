import csv
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from interactions.models import InteractionEvent


class Command(BaseCommand):
    help = "Export interaction behavior data to CSV (default: data_100user.csv)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="data_100user.csv",
            help="Output CSV path. Relative paths are resolved from interaction-service root.",
        )
        parser.add_argument(
            "--source",
            default="synthetic",
            help="Filter by source. Use --source all to export all sources.",
        )
        parser.add_argument(
            "--user-count",
            type=int,
            default=100,
            help="Number of distinct users to include (ordered by user_id). Use 0 for all users.",
        )

    def handle(self, *args, **options):
        output_path = self._resolve_output_path(options["output"])
        source = str(options["source"]).strip()
        user_count = int(options["user_count"])

        if user_count < 0:
            raise CommandError("--user-count must be >= 0")

        queryset = InteractionEvent.objects.all().order_by("timestamp", "id")
        if source and source.lower() != "all":
            queryset = queryset.filter(source=source)

        queryset = queryset.exclude(user_id__isnull=True)

        if user_count > 0:
            selected_user_ids = list(
                queryset.values_list("user_id", flat=True).distinct().order_by("user_id")[:user_count]
            )
            if not selected_user_ids:
                raise CommandError("No events matched selected filters; nothing to export.")
            queryset = queryset.filter(user_id__in=selected_user_ids)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        headers = [
            "event_id",
            "event_type",
            "user_id",
            "session_id",
            "product_id",
            "query_text",
            "source",
            "signal_weight",
            "timestamp",
            "metadata_json",
        ]

        row_count = 0
        user_ids = set()
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            for event in queryset.iterator(chunk_size=1000):
                row_count += 1
                user_ids.add(event.user_id)
                writer.writerow(
                    {
                        "event_id": str(event.event_id),
                        "event_type": event.event_type,
                        "user_id": event.user_id,
                        "session_id": event.session_id or "",
                        "product_id": event.product_id if event.product_id is not None else "",
                        "query_text": event.query_text or "",
                        "source": event.source,
                        "signal_weight": event.signal_weight,
                        "timestamp": event.timestamp.isoformat(),
                        "metadata_json": json.dumps(event.metadata or {}, ensure_ascii=True, sort_keys=True),
                    }
                )

        if row_count == 0:
            raise CommandError("No rows exported. Adjust filters or generate behavior data first.")

        self.stdout.write(self.style.SUCCESS("Behavior CSV export completed."))
        self.stdout.write(f"output={output_path}")
        self.stdout.write(f"rows={row_count}")
        self.stdout.write(f"distinct_users={len(user_ids)}")

    def _resolve_output_path(self, raw_path):
        target = Path(str(raw_path)).expanduser()
        if target.is_absolute():
            return target
        base_dir = Path(getattr(settings, "BASE_DIR", "."))
        return (base_dir / target).resolve()