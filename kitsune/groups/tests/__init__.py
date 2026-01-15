import factory

from kitsune.groups.models import GroupProfile
from kitsune.users.tests import GroupFactory


class GroupProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GroupProfile

    group = factory.SubFactory(GroupFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class.add_root(**kwargs)
