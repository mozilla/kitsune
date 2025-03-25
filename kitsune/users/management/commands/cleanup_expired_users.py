from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from kitsune.users.utils import delete_user_pipeline


class Command(BaseCommand):
    help = "Delete users who haven't logged in for more than settings.USER_EXPIRATION_DAYS days"

    def handle(self, *args, **options):
        User = get_user_model()
        expiration_date = timezone.now() - timedelta(days=settings.USER_EXPIRATION_DAYS)

        expired_users = User.objects.filter(last_login__lt=expiration_date)
        self.stdout.write(f"Found {expired_users.count()} expired users")

        for user in expired_users:
            delete_user_pipeline(user)
            self.stdout.write(f"Deleted user {user.username}")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully processed {expired_users.count()} expired users")
        )
