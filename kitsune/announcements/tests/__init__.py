from datetime import datetime, timedelta

from kitsune.announcements.models import Announcement
from kitsune.sumo.tests import with_save
from kitsune.users.tests import user


@with_save
def announcement(visible_dates=True, **kwargs):
    # Pass in visible_dates=False to hide the announcement.
    if visible_dates:
        defaults = {'show_after': datetime.now() - timedelta(days=2)}
    else:
        defaults = {'show_after': datetime.now() - timedelta(days=4),
                    'show_until': datetime.now() - timedelta(days=2)}
    defaults['content'] = ("*crackles* Captain's log, stardate 43124.5 "
                           "We are doomed.")
    if 'creator' not in kwargs:
        defaults['creator'] = user(save=True)
    defaults.update(kwargs)
    return Announcement(**defaults)
