import cronjobs
from datetime import datetime, timedelta

from rest_framework.authtoken.models import Token

from kitsune.questions.models import Answer
from kitsune.search.models import generate_tasks
from kitsune.search.tasks import index_task
from kitsune.users.models import RegistrationProfile, UserMappingType
from kitsune.wiki.models import Revision


@cronjobs.register
def remove_expired_registration_profiles():
    """"Cleanup expired registration profiles and users that not activated."""
    RegistrationProfile.objects.delete_expired_users()
    generate_tasks()


@cronjobs.register
def reindex_users_that_contributed_yesterday():
    """Update the users (in ES) that contributed yesterday.

    The idea is to update the last_contribution_date field.
    """
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    # Support Forum answers
    user_ids = list(Answer.objects.filter(
        created__gte=yesterday,
        created__lt=today).values_list('creator_id', flat=True))

    # KB Edits
    user_ids += list(Revision.objects.filter(
        created__gte=yesterday,
        created__lt=today).values_list('creator_id', flat=True))

    # KB Reviews
    user_ids += list(Revision.objects.filter(
        reviewed__gte=yesterday,
        reviewed__lt=today).values_list('reviewer_id', flat=True))

    # Note:
    # Army of Awesome replies are live indexed. No need to do anything here.

    index_task.delay(UserMappingType, list(set(user_ids)))


@cronjobs.register
def clear_expired_auth_tokens():
    too_old = datetime.now() - timedelta(days=30)
    Token.objects.filter(created__lt=too_old).delete()
