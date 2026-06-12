import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recommendations.deep_model_training import (
    load_jsonl,
    save_training_artifacts,
    train_model_from_splits,
)


class Command(BaseCommand):
    help = "Train Plan 11B deep ranking MVP model from Plan 11A dataset artifacts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset-dir",
            default=str(Path(settings.BASE_DIR) / "artifacts" / "deep_model" / "11a"),
            help="Directory containing dataset_train/valid/test jsonl from Plan 11A.",
        )
        parser.add_argument(
            "--output-dir",
            default=str(Path(settings.BASE_DIR) / "artifacts" / "deep_model" / "11b"),
            help="Directory where model artifacts and reports will be written.",
        )
        parser.add_argument("--model-version", default="plan11b-mlp-v1")
        parser.add_argument("--epochs", type=int, default=120)
        parser.add_argument("--batch-size", type=int, default=16)
        parser.add_argument("--learning-rate", type=float, default=0.01)
        parser.add_argument("--hidden-dims", default="32,16")
        parser.add_argument("--dropout", type=float, default=0.1)
        parser.add_argument("--patience", type=int, default=15)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, **options):
        dataset_dir = Path(options["dataset_dir"]).resolve()
        output_dir = Path(options["output_dir"]).resolve()
        model_version = str(options["model_version"])

        if not dataset_dir.exists():
            raise CommandError("dataset_dir does not exist: %s" % dataset_dir)

        train_rows = self._require_rows(dataset_dir / "dataset_train.jsonl")
        valid_rows = self._require_rows(dataset_dir / "dataset_valid.jsonl")
        test_rows = self._require_rows(dataset_dir / "dataset_test.jsonl")

        hidden_dims = self._parse_hidden_dims(options["hidden_dims"])
        config = {
            "epochs": int(options["epochs"]),
            "batch_size": int(options["batch_size"]),
            "learning_rate": float(options["learning_rate"]),
            "hidden_dims": hidden_dims,
            "dropout": float(options["dropout"]),
            "patience": int(options["patience"]),
            "seed": int(options["seed"]),
        }
        self._validate_config(config)

        protocol = {}
        protocol_path = dataset_dir / "protocol.json"
        if protocol_path.exists():
            protocol = json.loads(protocol_path.read_text(encoding="utf-8"))

        model_bundle = train_model_from_splits(
            train_rows,
            valid_rows,
            test_rows,
            config=config,
        )
        artifact_summary = save_training_artifacts(
            output_dir=output_dir,
            model_bundle=model_bundle,
            config=config,
            protocol=protocol,
            model_version=model_version,
        )

        metrics = artifact_summary["metrics_report"]
        self.stdout.write(self.style.SUCCESS("Plan 11B model training completed."))
        self.stdout.write("output_dir=%s" % artifact_summary["output_dir"])
        self.stdout.write(
            "test: auc=%s f1=%s recall@5=%s ndcg@10=%s"
            % (
                metrics["test"]["auc"],
                metrics["test"]["f1"],
                metrics["test"]["recall_at_5"],
                metrics["test"]["ndcg_at_10"],
            )
        )
        self.stdout.write("model_version=%s" % artifact_summary["model_version"])

    def _require_rows(self, path):
        rows = load_jsonl(path)
        if not rows:
            raise CommandError("Dataset split is empty or missing: %s" % path)
        return rows

    def _parse_hidden_dims(self, raw):
        tokens = [token.strip() for token in str(raw).split(",")]
        dims = []
        for token in tokens:
            if not token:
                continue
            try:
                value = int(token)
            except ValueError as exc:
                raise CommandError("Invalid --hidden-dims token: %s" % token) from exc
            dims.append(value)
        if not dims:
            raise CommandError("--hidden-dims must contain at least one positive integer")
        if any(value <= 0 for value in dims):
            raise CommandError("--hidden-dims values must be > 0")
        return dims

    def _validate_config(self, config):
        if config["epochs"] <= 0:
            raise CommandError("--epochs must be > 0")
        if config["batch_size"] <= 0:
            raise CommandError("--batch-size must be > 0")
        if config["learning_rate"] <= 0:
            raise CommandError("--learning-rate must be > 0")
        if config["dropout"] < 0 or config["dropout"] >= 1:
            raise CommandError("--dropout must satisfy 0 <= dropout < 1")
        if config["patience"] <= 0:
            raise CommandError("--patience must be > 0")
