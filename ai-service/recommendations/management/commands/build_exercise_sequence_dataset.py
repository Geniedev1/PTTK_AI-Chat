import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recommendations.exercise_sequence_dataset import (
    build_sequence_artifacts,
    save_sequence_artifacts,
)


class Command(BaseCommand):
    help = "Build Plan 03 sequence dataset artifacts for exercise RNN/LSTM/biLSTM models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input-csv",
            default=str(Path(settings.BASE_DIR).parent / "interaction-service" / "data_user500_full.csv"),
        )
        parser.add_argument(
            "--output-dir",
            default=str(Path(settings.BASE_DIR) / "artifacts" / "exercise_sequence"),
        )
        parser.add_argument("--max-sequence-length", type=int, default=12)
        parser.add_argument("--prediction-horizon", type=int, default=3)
        parser.add_argument("--min-history", type=int, default=2)
        parser.add_argument("--train-ratio", type=float, default=0.7)
        parser.add_argument("--valid-ratio", type=float, default=0.15)

    def handle(self, *args, **options):
        input_csv = Path(options["input_csv"]).resolve()
        output_dir = Path(options["output_dir"]).resolve()

        if not input_csv.exists():
            raise CommandError("input csv does not exist: %s" % input_csv)

        bundle = build_sequence_artifacts(
            input_csv,
            max_sequence_length=int(options["max_sequence_length"]),
            prediction_horizon=int(options["prediction_horizon"]),
            min_history=int(options["min_history"]),
            train_ratio=float(options["train_ratio"]),
            valid_ratio=float(options["valid_ratio"]),
        )
        if bundle["stats"]["sample_count"] == 0:
            raise CommandError("Sequence dataset builder produced 0 samples.")

        result = save_sequence_artifacts(output_dir, bundle)

        self.stdout.write(self.style.SUCCESS("Exercise sequence dataset build completed."))
        self.stdout.write("output_dir=%s" % result["output_dir"])
        self.stdout.write(
            "samples=%s actors=%s positive_rate=%s"
            % (
                result["stats"]["sample_count"],
                result["stats"]["actor_count"],
                result["stats"]["positive_rate"],
            )
        )
        self.stdout.write(
            "split=%s"
            % json.dumps(result["stats"]["split"]["sample_split_counts"], ensure_ascii=True, sort_keys=True)
        )
