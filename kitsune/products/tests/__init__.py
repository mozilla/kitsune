# -*- coding: utf-8 -*-
import factory.django
import factory.fuzzy
from django.template.defaultfilters import slugify

from kitsune.products.models import Product
from kitsune.products.models import Topic
from kitsune.products.models import Version
from kitsune.sumo.tests import FuzzyUnicode


class ProductFactory(factory.DjangoModelFactory):
    class Meta:
        model = Product

    title = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    description = FuzzyUnicode()
    display_order = factory.fuzzy.FuzzyInteger(10)
    visible = True

    image = factory.django.ImageField()
    image_offset = 0
    image_cachebuster = FuzzyUnicode()
    sprite_height = 100


class TopicFactory(factory.DjangoModelFactory):
    class Meta:
        model = Topic

    title = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    description = FuzzyUnicode()
    image = factory.django.ImageField()
    product = factory.SubFactory(ProductFactory)
    display_order = factory.fuzzy.FuzzyInteger(10)
    visible = True
    in_aaq = factory.fuzzy.FuzzyChoice([True, False])


class VersionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Version

    min_version = factory.fuzzy.FuzzyDecimal(100)
    max_version = factory.LazyAttribute(lambda obj: obj.min_version + 1)
    name = factory.LazyAttribute(lambda obj: 'Version %d' % obj.min_version)
    slug = factory.LazyAttribute(lambda obj: 'v%d' % obj.min_version)
    visible = True
    default = factory.fuzzy.FuzzyChoice([False, True])
    product = factory.SubFactory(ProductFactory)
