import factory

from kitsune.groups.models import GroupProfile
from kitsune.users.tests import GroupFactory


class GroupProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = GroupProfile

    group = factory.SubFactory(GroupFactory)
