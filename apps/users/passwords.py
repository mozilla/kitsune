import string
import re

from django.core.cache import cache
from django.conf import settings


PASSWORD_CACHE_KEY = 'password-blacklist'
USERNAME_CACHE_KEY = 'username-blacklist'


def username_allowed(username=''):
    """Returns True if the given username is not a blatent bad word."""
    blacklist = cache.get(USERNAME_CACHE_KEY)
    if blacklist is None:
        f = open(settings.USERNAME_BLACKLIST, 'r')
        blacklist = [w.strip() for w in f.readlines()]
        cache.set(USERNAME_CACHE_KEY, blacklist)
    username = username.lower()
    usernames = set([username])
    usernames |= set(''.join([o for o in username
                           if not o in string.punctuation]).split())
    usernames |= set(re.findall(r'\w+', username))
    return not usernames.intersection(blacklist)


def password_allowed(password):
    blacklist = cache.get(PASSWORD_CACHE_KEY)
    if blacklist is None:
        f = open(settings.PASSWORD_BLACKLIST, 'r')
        blacklist = [w.strip() for w in f.readlines()]
        cache.set(PASSWORD_CACHE_KEY, blacklist)
    return password not in blacklist
