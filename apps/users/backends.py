from django.contrib.auth.backends import ModelBackend


# Live sessions will still be using this backend for a while.
# TODO: Remove after there are no more sessions using this in prod.
class Sha256Backend(ModelBackend):
    """Overriding the Django model backend without changes."""
    pass
