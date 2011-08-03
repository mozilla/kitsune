from django.contrib.auth.models import AnonymousUser


class NamedAnonymousUser(AnonymousUser):
    """A user not mapped to a known persistent user but having a name for
    display purposes"""
    def __init__(self, username):
        self.username = username
