import json

from django.core.management.base import BaseCommand, CommandError

from recommendations.services import RecommendationService


class Command(BaseCommand):
    help = "Build behavioral profile snapshot for a user or session scope."
    service_class = RecommendationService

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int, dest="user_id")
        parser.add_argument("--session-id", type=str, dest="session_id")
        parser.add_argument(
            "--pretty",
            action="store_true",
            help="Pretty-print JSON output.",
        )

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        session_id = options.get("session_id")
        pretty = options.get("pretty", False)

        if user_id is None and not session_id:
            raise CommandError("Provide --user-id or --session-id.")

        payload = self.service_class().get_profile_snapshot(
            user_id=user_id,
            session_id=session_id,
        )

        if pretty:
            content = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
        else:
            content = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        self.stdout.write(content)
