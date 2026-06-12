import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from interactions.exercise_behavior import (
    EXERCISE_SUBMISSION_HEADERS,
    FULL_EXPORT_HEADERS,
    build_submission_quality_report,
    event_to_full_row,
    event_to_submission_row,
    write_csv,
)
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
        parser.add_argument(
            "--mode",
            choices=["full", "submission"],
            default="full",
            help="full = internal event export, submission = user_id/product_id/action/timestamp format for exercise.",
        )
        parser.add_argument(
            "--quality-report",
            default="",
            help="Optional JSON report path. Mainly used with --mode submission.",
        )

    def handle(self, *args, **options):
        output_path = self._resolve_output_path(options["output"])
        source = str(options["source"]).strip()
        user_count = int(options["user_count"])
        mode = str(options["mode"]).strip()
        quality_report_path = str(options["quality_report"]).strip()

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

        rows = []
        user_ids = set()
        for event in queryset.iterator(chunk_size=1000):
            if mode == "submission":
                row = event_to_submission_row(event)
            else:
                row = event_to_full_row(event)
            if row is None:
                continue
            rows.append(row)
            if row.get("user_id") not in ("", None):
                user_ids.add(int(row["user_id"]))

        if not rows:
            raise CommandError("No rows exported. Adjust filters or generate behavior data first.")

        headers = EXERCISE_SUBMISSION_HEADERS if mode == "submission" else FULL_EXPORT_HEADERS
        write_csv(output_path, headers, rows)

        if quality_report_path:
            quality_path = self._resolve_output_path(quality_report_path)
            quality_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {}
            if mode == "submission":
                payload = build_submission_quality_report(rows)
                payload["output"] = str(output_path)
                payload["mode"] = mode
                quality_path.write_text(
                    json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
            else:
                quality_path.write_text(
                    json.dumps(
                        {
                            "output": str(output_path),
                            "mode": mode,
                            "row_count": len(rows),
                            "distinct_user_count": len(user_ids),
                        },
                        ensure_ascii=True,
                        indent=2,
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )

        self.stdout.write(self.style.SUCCESS("Behavior CSV export completed."))
        self.stdout.write(f"output={output_path}")
        self.stdout.write(f"rows={len(rows)}")
        self.stdout.write(f"distinct_users={len(user_ids)}")
        self.stdout.write(f"mode={mode}")

    def _resolve_output_path(self, raw_path):
        target = Path(str(raw_path)).expanduser()
        if target.is_absolute():
            return target
        base_dir = Path(getattr(settings, "BASE_DIR", "."))
        return (base_dir / target).resolve()
