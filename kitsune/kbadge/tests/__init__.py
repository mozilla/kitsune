from badger.models import Award, Badge

from kitsune.sumo.tests import with_save
from kitsune.users.tests import profile


@with_save
def award(**kwargs):
    # TODO: factory for award
    defaults = {
        'description': u'An award!',
    }
    defaults.update(kwargs)

    if 'badge' not in defaults:
        defaults['badge'] = badge(with_save=True)

    if 'user' not in defaults:
        defaults['user'] = profile().user

    return Award(**defaults)


@with_save
def badge(**kwargs):
    defaults = {
        'title': u'BADGE!',
        'description': u'A badge',
    }
    defaults.update(kwargs)

    return Badge(**defaults)
