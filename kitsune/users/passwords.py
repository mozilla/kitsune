import re

from django.core.cache import cache
from django.conf import settings


USERNAME_CACHE_KEY = 'username-blacklist'


def username_allowed(username):
    if not username:
        return False
    """Returns True if the given username is not a blatent bad word."""
    blacklist = cache.get(USERNAME_CACHE_KEY)
    if blacklist is None:
        f = open(settings.USERNAME_BLACKLIST, 'r')
        blacklist = [w.strip() for w in f.readlines()]
        cache.set(USERNAME_CACHE_KEY, blacklist, 60 * 60)  # 1 hour
    # Lowercase
    username = username.lower()
    # Add lowercased and non alphanumerics to start.
    usernames = set([username, re.sub("\W", "", username)])
    # Add words split on non alphanumerics.
    for u in re.findall(r'\w+', username):
        usernames.add(u)
    # Do any match the bad words?
    return not usernames.intersection(blacklist)
