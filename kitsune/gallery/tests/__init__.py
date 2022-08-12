import factory

from kitsune.gallery.models import Image, Video
from kitsune.sumo.tests import FuzzyUnicode
from kitsune.users.tests import UserFactory


class ImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Image

    creator = factory.SubFactory(UserFactory)
    description = FuzzyUnicode()
    file = factory.django.ImageField()
    title = FuzzyUnicode()


class VideoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Video

    creator = factory.SubFactory(UserFactory)
    webm = factory.django.FileField(from_path="kitsune/gallery/tests/media/test.webm")
    ogv = factory.django.FileField(from_path="kitsune/gallery/tests/media/test.ogv")
    flv = factory.django.FileField(from_path="kitsune/gallery/tests/media/test.flv")
