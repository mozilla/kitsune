from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from kitsune.flagit.models import FlaggedObject
from kitsune.forums.models import Post, Thread
from kitsune.users.handlers import UserDeletionListener
from kitsune.users.models import Profile


class ThreadListener(UserDeletionListener):
    """Handles thread cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        # First get all threads that should be reassigned, then delete the rest
        Thread.objects.filter(creator=user, replies__gt=0).update(creator=Profile.get_sumo_bot())
        Thread.objects.filter(creator=user).delete()


class PostListener(UserDeletionListener):
    """Handles post cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        posts = Post.objects.filter(author=user)

        post_content_type = ContentType.objects.get_for_model(Post)

        flagged_posts = Post.objects.filter(
            id__in=FlaggedObject.objects.filter(
                content_type=post_content_type, object_id__in=posts.values_list("id", flat=True)
            ).values_list("object_id", flat=True)
        )

        for post in flagged_posts:
            post.delete()

        Post.objects.filter(author=user).exclude(
            id__in=flagged_posts.values_list("id", flat=True)
        ).update(author=Profile.get_sumo_bot())
