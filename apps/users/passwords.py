from django.core.cache import cache
from django.conf import settings


CACHE_KEY = 'password-blacklist'


def password_allowed(password):
    blacklist = cache.get(CACHE_KEY)
    if blacklist is None:
        f = open(settings.PASSWORD_BLACKLIST, 'r')
        blacklist = [w.strip() for w in f.readlines()]
        cache.set(CACHE_KEY, blacklist)
    return password not in blacklist
