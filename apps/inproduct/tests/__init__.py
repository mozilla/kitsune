from inproduct.models import Redirect
from sumo.tests import with_save


@with_save
def redirect(**kwargs):
    """Return an inproduct redirect."""
    defaults = {'target': 'home'}
    defaults.update(kwargs)

    return Redirect(**defaults)
