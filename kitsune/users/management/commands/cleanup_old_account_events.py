from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from kitsune.users.models import AccountEvent


class Command(BaseCommand):
    help = "Deletes account events that are older than two years"

    def handle(self, *args, **options):
        two_years_ago = timezone.now() - timedelta(days=730)  # 2 years * 365 days
        deleted_count = AccountEvent.objects.filter(created_at__lt=two_years_ago).delete()[0]
        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {deleted_count} old account events")
        )
