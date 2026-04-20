import json
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command

from interactions.exercise_behavior import build_submission_quality_report


class Command(BaseCommand):
    help = "Generate 500-user synthetic behavior data and export exercise submission/full CSV artifacts."

    def add_arguments(self, parser):
        base_dir = Path(settings.BASE_DIR)
        parser.add_argument("--users", type=int, default=500)
        parser.add_argument("--sessions-per-user", type=int, default=4)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--lookback-days", type=int, default=45)
        parser.add_argument("--source", default="synthetic-exercise")
        parser.add_argument(
            "--submission-output",
            default=str(base_dir / "data_user500.csv"),
        )
        parser.add_argument(
            "--full-output",
            default=str(base_dir / "data_user500_full.csv"),
        )
        parser.add_argument(
            "--quality-report",
            default=str(base_dir / "data_user500_quality_report.json"),
        )

    def handle(self, *args, **options):
        users = int(options["users"])
        if users < 500:
            raise CommandError("--users must be >= 500 for exercise submission output.")

        source = str(options["source"]).strip() or "synthetic-exercise"
        submission_output = Path(options["submission_output"]).resolve()
        full_output = Path(options["full_output"]).resolve()
        quality_report = Path(options["quality_report"]).resolve()

        call_command(
            "generate_synthetic_behavior",
            users=users,
            sessions_per_user=int(options["sessions_per_user"]),
            lookback_days=int(options["lookback_days"]),
            seed=int(options["seed"]),
            source=source,
            clear_source=True,
            stdout=self.stdout,
        )

        call_command(
            "export_behavior_csv",
            output=str(full_output),
            source=source,
            user_count=users,
            mode="full",
            stdout=self.stdout,
        )

        call_command(
            "export_behavior_csv",
            output=str(submission_output),
            source=source,
            user_count=users,
            mode="submission",
            quality_report=str(quality_report),
            stdout=self.stdout,
        )

        report_payload = json.loads(quality_report.read_text(encoding="utf-8"))
        self.stdout.write(self.style.SUCCESS("Exercise data_user500 build completed."))
        self.stdout.write("submission_output=%s" % submission_output)
        self.stdout.write("full_output=%s" % full_output)
        self.stdout.write("quality_report=%s" % quality_report)
        self.stdout.write(
            "acceptance: users=%s behaviors=%s row_count=%s"
            % (
                report_payload["distinct_user_count"],
                report_payload["distinct_action_count"],
                report_payload["row_count"],
            )
        )
