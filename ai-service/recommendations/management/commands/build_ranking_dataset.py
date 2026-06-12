import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recommendations.deep_dataset import (
    LABEL_EVENT_SCORES,
    build_dataset_records,
    build_quality_report,
    split_samples_by_actor_time,
)
from recommendations.services import InteractionAnalyticsClient, ProductCatalogClient


class Command(BaseCommand):
    help = "Build reproducible train/valid/test ranking dataset for Plan 11A."

    product_client_class = ProductCatalogClient
    interaction_client_class = InteractionAnalyticsClient

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default=str(Path(settings.BASE_DIR) / "artifacts" / "deep_model" / "11a"),
            help="Directory for dataset and reports.",
        )
        parser.add_argument("--events-limit", type=int, default=200)
        parser.add_argument("--label-window-days", type=int, default=14)
        parser.add_argument("--train-ratio", type=float, default=0.7)
        parser.add_argument("--valid-ratio", type=float, default=0.15)

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"]).resolve()
        events_limit = int(options["events_limit"])
        label_window_days = int(options["label_window_days"])
        train_ratio = float(options["train_ratio"])
        valid_ratio = float(options["valid_ratio"])

        if events_limit <= 0:
            raise CommandError("--events-limit must be > 0")
        if label_window_days <= 0:
            raise CommandError("--label-window-days must be > 0")
        if train_ratio <= 0 or valid_ratio < 0 or train_ratio + valid_ratio >= 1.0:
            raise CommandError("Require 0 < train_ratio, 0 <= valid_ratio, and train_ratio + valid_ratio < 1")

        interaction_client = self.interaction_client_class()
        product_client = self.product_client_class()

        events = interaction_client.fetch_all_events(limit=events_limit)
        products = product_client.fetch_products()
        if not events:
            raise CommandError("No interaction events found for dataset build.")
        if not products:
            raise CommandError("No products found for dataset build.")

        records = build_dataset_records(
            events,
            products,
            label_window_days=label_window_days,
        )
        if not records:
            raise CommandError("Dataset builder produced 0 records; check event coverage.")

        splits, split_meta = split_samples_by_actor_time(
            records,
            train_ratio=train_ratio,
            valid_ratio=valid_ratio,
        )
        quality_report = build_quality_report(records, splits)

        output_dir.mkdir(parents=True, exist_ok=True)
        self._write_jsonl(output_dir / "dataset_train.jsonl", splits["train"])
        self._write_jsonl(output_dir / "dataset_valid.jsonl", splits["valid"])
        self._write_jsonl(output_dir / "dataset_test.jsonl", splits["test"])

        protocol = {
            "plan": "11A",
            "sample_unit": "actor_item",
            "label_window_days": label_window_days,
            "label_event_scores": LABEL_EVENT_SCORES,
            "split": split_meta,
            "record_count": len(records),
            "feature_version": "plan11a-v1",
        }
        (output_dir / "protocol.json").write_text(
            json.dumps(protocol, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (output_dir / "quality_report.json").write_text(
            json.dumps(quality_report, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        self.stdout.write(self.style.SUCCESS("Plan 11A dataset build completed."))
        self.stdout.write("output_dir=%s" % output_dir)
        self.stdout.write(
            "records=%s train=%s valid=%s test=%s"
            % (
                len(records),
                len(splits["train"]),
                len(splits["valid"]),
                len(splits["test"]),
            )
        )
        self.stdout.write(
            "quality: positives=%s weak_negatives=%s leakage_ok=%s"
            % (
                quality_report["class_balance"]["binary_positive_count"],
                quality_report["class_balance"]["weak_negative_count"],
                quality_report["leakage_check"]["passed"],
            )
        )

    def _write_jsonl(self, path, rows):
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True))
                handle.write("\n")
