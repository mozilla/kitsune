notification_handlers = set()


def notification_handler(fn):
    """
    Register a function to be called via Celery for every notification.

    This may be used as a decorator or as a simple function.
    """
    notification_handlers.add(fn)
    return fn
