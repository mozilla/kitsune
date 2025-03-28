from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from kitsune.flagit.models import FlaggedObject
from kitsune.users.handlers import UserDeletionListener


class FlagListener(UserDeletionListener):
    """Handles flag cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        """
        When a user is deleted:
        - Delete flags where the user was the content object
        """
        user_content_type = ContentType.objects.get_for_model(User)
        FlaggedObject.objects.filter(content_type=user_content_type, object_id=user.id).delete()
