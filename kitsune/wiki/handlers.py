from django.conf import settings
from django.contrib.auth.models import Group, User

from kitsune.users.handlers import UserDeletionListener
from kitsune.wiki.models import Document, Revision


class DocumentListener(UserDeletionListener):
    """Listener for document-related tasks."""

    def on_user_deletion(self, user: User) -> None:
        """Handle the deletion of a user."""

        documents = Document.objects.filter(contributors=user)
        content_group = Group.objects.get(name=settings.SUMO_CONTENT_GROUP)
        for document in documents:
            if not document.contributors.exclude(id=user.id).exists():
                document.contributors.add(*content_group.user_set.all())
            document.contributors.remove(user)

        try:
            sumo_bot = User.objects.get(username=settings.SUMO_BOT_USERNAME)
        except User.DoesNotExist:
            raise ValueError("SumoBot user not found")
        else:
            Revision.objects.filter(creator=user).update(creator=sumo_bot)
