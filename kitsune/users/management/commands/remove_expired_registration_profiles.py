from django.core.management.base import BaseCommand

from kitsune.search.models import generate_tasks
from kitsune.users.models import RegistrationProfile


class Command(BaseCommand):
    help = "Cleanup expired registration profiles and users that not activated."

    def handle(self, **options):
        RegistrationProfile.objects.delete_expired_users()
        generate_tasks()
