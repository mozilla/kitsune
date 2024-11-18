import factory
from django.template.defaultfilters import slugify

from kitsune.sumo.tests import FuzzyUnicode
from kitsune.tags.models import SumoTag


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SumoTag

    name = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
