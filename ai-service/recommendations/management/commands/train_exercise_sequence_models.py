import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recommendations.exercise_sequence_models import (
    copy_best_model,
    load_sequence_npz,
    save_model_artifacts,
    select_best_model,
    train_model,
    write_comparison_report,
)


class Command(BaseCommand):
    help = "Train exercise sequence models: RNN, LSTM, biLSTM, GRU, CNN1D, Attention."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset-dir",
            default=str(Path(settings.BASE_DIR) / "artifacts" / "exercise_sequence"),
        )
        parser.add_argument(
            "--output-dir",
            default=str(Path(settings.BASE_DIR) / "artifacts" / "exercise_models"),
        )
        parser.add_argument("--hidden-dim", type=int, default=16)
        parser.add_argument("--epochs", type=int, default=8)
        parser.add_argument("--learning-rate", type=float, default=0.01)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, **options):
        dataset_dir = Path(options["dataset_dir"]).resolve()
        output_dir = Path(options["output_dir"]).resolve()
        if not dataset_dir.exists():
            raise CommandError("dataset_dir does not exist: %s" % dataset_dir)

        preprocess_config_path = dataset_dir / "preprocess_config.json"
        if not preprocess_config_path.exists():
            raise CommandError("Missing preprocess_config.json in dataset_dir.")

        preprocess_config = json.loads(preprocess_config_path.read_text(encoding="utf-8"))
        train_payload = load_sequence_npz(dataset_dir / "train.npz")
        valid_payload = load_sequence_npz(dataset_dir / "valid.npz")
        test_payload = load_sequence_npz(dataset_dir / "test.npz")

        model_reports = []
        common_config = {
            "hidden_dim": int(options["hidden_dim"]),
            "epochs": int(options["epochs"]),
            "learning_rate": float(options["learning_rate"]),
            "seed": int(options["seed"]),
        }

        for model_type in ("rnn", "lstm", "bilstm", "gru", "cnn1d", "attention"):
            model, metrics = train_model(
                train_payload,
                valid_payload,
                test_payload,
                preprocess_config,
                model_type=model_type,
                hidden_dim=common_config["hidden_dim"],
                epochs=common_config["epochs"],
                learning_rate=common_config["learning_rate"],
                seed=common_config["seed"],
            )
            model_dir = output_dir / model_type
            save_model_artifacts(
                model_dir,
                model_type=model_type,
                model=model,
                metrics=metrics,
                config={**common_config, "model_type": model_type},
            )
            model_reports.append({"model_type": model_type, "metrics": metrics})

        best = select_best_model(model_reports)
        write_comparison_report(output_dir, model_reports, best)
        copy_best_model(output_dir, best["model_type"])

        self.stdout.write(self.style.SUCCESS("Exercise sequence model training completed."))
        self.stdout.write("output_dir=%s" % output_dir)
        self.stdout.write("model_best=%s" % best["model_type"])
        self.stdout.write(
            "valid_f1=%s valid_auc=%s"
            % (best["metrics"]["valid"]["f1"], best["metrics"]["valid"]["auc"])
        )
