from actstream.models import Action

from kitsune.notifications.models import Notification
from kitsune.users.tests import profile
from kitsune.sumo.tests import with_save


@with_save
def notification(**kwargs):
    """Create and return a notification."""
    defaults = {
        'read_at': None,
    }
    defaults.update(kwargs)

    if 'owner' not in defaults:
        defaults['owner'] = profile().user
    if 'action' not in defaults:
        defaults['action'] = Action.objects.create(actor=profile().user, verb='looked at')

    return Notification(**defaults)
