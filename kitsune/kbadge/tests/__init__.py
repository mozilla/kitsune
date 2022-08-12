import factory

from kitsune.kbadge.models import Award, Badge
from kitsune.sumo.tests import FuzzyUnicode
from kitsune.users.tests import UserFactory


class BadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Badge

    description = FuzzyUnicode()
    title = FuzzyUnicode()


class AwardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Award

    badge = factory.SubFactory(BadgeFactory)
    description = FuzzyUnicode()
    user = factory.SubFactory(UserFactory)
