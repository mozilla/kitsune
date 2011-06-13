from groups.models import GroupProfile
from sumo.tests import with_save


@with_save
def group_profile(**kwargs):
    return GroupProfile(**kwargs)
