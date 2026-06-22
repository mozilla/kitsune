import factory

from kitsune.gallery.models import Image
from kitsune.sumo.tests import FuzzyUnicode
from kitsune.users.tests import UserFactory


class ImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Image

    creator = factory.SubFactory(UserFactory)
    description = FuzzyUnicode()
    file = factory.django.ImageField()
    title = FuzzyUnicode()
