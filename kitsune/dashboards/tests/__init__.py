from django.contrib.auth.models import Group

from kitsune.dashboards.models import GroupDashboard
from kitsune.dashboards.personal import LocaleDashboard


def group_dashboard(save=False, **kwargs):
    """Create a group dashboard model instance and return it.

    Assumes a group already exists.

    """
    defaults = {'group': kwargs.pop('group', None) or Group.objects.all()[0],
                'dashboard': LocaleDashboard.slug,
                'parameters': 'de'}
    defaults.update(kwargs)
    gd = GroupDashboard(**defaults)
    if save:
        gd.save()
    return gd
