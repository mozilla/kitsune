from jingo import register

from kitsune.kbforums.events import NewPostInLocaleEvent


@register.function
def is_watching_discussion_locale(user, locale):
    """Return True if `user` is watching the discussion for `locale` and
    False, otherwise."""
    return NewPostInLocaleEvent.is_notifying(user, locale=locale)
