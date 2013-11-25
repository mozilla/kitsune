import cronjobs

from kitsune.search.models import generate_tasks
from kitsune.users.models import RegistrationProfile


@cronjobs.register
def remove_expired_registration_profiles():
    """"Cleanup expired registration profiles and users that not activated."""
    RegistrationProfile.objects.delete_expired_users()
    generate_tasks()
