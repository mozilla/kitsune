from django.contrib.auth.models import User

from kitsune.gallery.models import Image, Video
from kitsune.users.handlers import UserDeletionListener
from kitsune.users.models import Profile


class MediaListener(UserDeletionListener):
    """Listener to transfer media to SumoBot when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        """Handle the deletion of a user."""

        sumo_bot = Profile.get_sumo_bot()
        Image.objects.filter(creator=user).update(creator=sumo_bot)
        Video.objects.filter(creator=user).update(creator=sumo_bot)
