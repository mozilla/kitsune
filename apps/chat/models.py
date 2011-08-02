from django.contrib.auth.models import AnonymousUser


class NamedAnonymousUser(AnonymousUser):
    username = 'Anonymous'
