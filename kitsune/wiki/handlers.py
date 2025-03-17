from django.conf import settings
from django.contrib.auth.models import Group, User

from kitsune.users.handlers import UserDeletionListener
from kitsune.users.models import Profile
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

        sumo_bot = Profile.get_sumo_bot()
        Revision.objects.filter(creator=user).update(creator=sumo_bot)
