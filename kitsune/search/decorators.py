from functools import wraps
from django.conf import settings


def search_receiver(signal, sender):
    """
    Returns a decorator which registers the decorated function as a receiver
    of the supplied signal and sender.

    The decorated function won't be called if the signal is sent when
    `settings.ES_LIVE_INDEXING = False`.

    The decorated function won't be called if the signal is an m2m_changed
    signal with a pre_ action.
    """

    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):

            if not settings.ES_LIVE_INDEXING:
                return

            if kwargs.get("action", "").startswith("pre_"):
                return

            return func(*args, **kwargs)

        dispatch_uid = f"{func.__module__}.{func.__name__}"
        signal.connect(wrapped_func, sender=sender, dispatch_uid=dispatch_uid)
        return wrapped_func

    return decorator
