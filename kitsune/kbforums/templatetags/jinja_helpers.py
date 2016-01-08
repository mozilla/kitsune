from django_jinja import library

from kitsune.kbforums.events import NewPostInLocaleEvent


@library.global_function
def is_watching_discussion_locale(user, locale):
    """Return True if `user` is watching the discussion for `locale` and
    False, otherwise."""
    return NewPostInLocaleEvent.is_notifying(user, locale=locale)
