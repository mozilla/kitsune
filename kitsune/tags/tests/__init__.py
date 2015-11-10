from django.template.defaultfilters import slugify

import factory
from taggit.models import Tag

from kitsune.sumo.tests import FuzzyUnicode


class TagFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tag

    name = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
