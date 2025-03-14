from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from kitsune.flagit.models import FlaggedObject
from kitsune.forums.models import Post, Thread
from kitsune.users.handlers import UserDeletionListener


class ThreadListener(UserDeletionListener):
    """Handles thread cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:

        sumo_bot = User.objects.get(username=settings.SUMO_BOT_USERNAME)
        Thread.objects.filter(creator=user).update(creator=sumo_bot)


class PostListener(UserDeletionListener):
    """Handles post cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        sumo_bot = User.objects.get(username=settings.SUMO_BOT_USERNAME)
        posts = Post.objects.filter(author=user)

        post_content_type = ContentType.objects.get_for_model(Post)

        flagged_posts = Post.objects.filter(
            id__in=FlaggedObject.objects.filter(
                content_type=post_content_type, object_id__in=posts.values_list("id", flat=True)
            ).values_list("object_id", flat=True)
        )

        # delete individual posts b/c of custom delete method
        for post in flagged_posts:
            post.delete()

        Post.objects.filter(author=user).exclude(
            id__in=flagged_posts.values_list("id", flat=True)
        ).update(author=sumo_bot)

        # Assuming that only trusted contributors can edit posts, we shouldn't
        # need to first delete any posts that have been updated by the user and
        # then flagged after the update.
        Post.objects.filter(updated_by=user).update(updated_by=sumo_bot)
