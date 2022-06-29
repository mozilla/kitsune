from zlib import crc32

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse as django_reverse
from django.utils.module_loading import import_string


def collate(*iterables, **kwargs):
    """Return an iterable ordered collation of the already-sorted items
    from each of ``iterables``, compared by kwarg ``key``.

    If ``reverse=True`` is passed, iterables must return their results in
    descending order rather than ascending.

    """
    key = kwargs.pop("key", lambda a: a)
    reverse = kwargs.pop("reverse", False)
    min_or_max = max if reverse else min

    rows = [iter(iterable) for iterable in iterables if iterable]
    next_values = {}
    by_key = []

    def gather_next_value(row, index):
        try:
            next_value = next(row)
        except StopIteration:
            pass
        else:
            next_values[index] = next_value
            by_key.append((key(next_value), index))

    for index, row in enumerate(rows):
        gather_next_value(row, index)

    while by_key:
        key_value, index = min_or_max(by_key)
        by_key.remove((key_value, index))
        next_value = next_values.pop(index)
        yield next_value
        gather_next_value(rows[index], index)


def hash_to_unsigned(data):
    """If ``data`` is a string or unicode string, return an unsigned 4-byte int
    hash of it. If ``data`` is already an int that fits those parameters,
    return it verbatim.

    If ``data`` is an int outside that range, behavior is undefined at the
    moment. We rely on the ``PositiveIntegerField`` on
    :class:`~tidings.models.WatchFilter` to scream if the int is too long for
    the field.

    We use CRC32 to do the hashing. Though CRC32 is not a good general-purpose
    hash function, it has no collisions on a dictionary of 38,470 English
    words, which should be fine for the small sets that :class:`WatchFilters
    <tidings.models.WatchFilter>` are designed to enumerate. As a bonus, it is
    fast and available as a built-in function in some DBs. If your set of
    filter values is very large or has different CRC32 distribution properties
    than English words, you might want to do your own hashing in your
    :class:`~tidings.events.Event` subclass and pass ints when specifying
    filter values.

    """
    if isinstance(data, str):
        # Return a CRC32 value identical across Python versions and platforms
        # by stripping the sign bit as on
        # http://docs.python.org/library/zlib.html.
        return crc32(data.encode("utf-8")) & 0xFFFFFFFF
    else:
        return int(data)


def import_from_setting(setting_name, fallback):
    """Return the resolution of an import path stored in a Django setting.

    :arg setting_name: The name of the setting holding the import path
    :arg fallback: An alternate object to use if the setting is empty or
      doesn't exist

    Raise ImproperlyConfigured if a path is given that can't be resolved.

    """
    path = getattr(settings, setting_name, None)
    if path:
        try:
            return import_string(path)
        except ImportError:
            raise ImproperlyConfigured("%s: No such path." % path)
    else:
        return fallback


# Here to be imported by others:
reverse = import_from_setting("TIDINGS_REVERSE", django_reverse)  # no QA


def get_users(user_ids):
    """
    Convenience function that returns a list of user objects for the given user ids.
    """
    if user_ids is None:
        return None
    return list(get_user_model().objects.filter(id__in=user_ids).all())
