# -*- coding: utf-8 -*-
import factory
import factory.django
import factory.fuzzy
from django.template.defaultfilters import slugify

from kitsune.products.models import Product, Topic, Version
from kitsune.sumo.tests import FuzzyUnicode


class ProductFactory(factory.django.DjangoModelFactory):
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


class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic

    title = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    description = FuzzyUnicode()
    image = factory.django.ImageField()
    display_order = factory.fuzzy.FuzzyInteger(10)
    visible = True
    in_aaq = factory.fuzzy.FuzzyChoice([True, False])

    @factory.post_generation
    def products(topic, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for t in extracted:
                topic.products.add(t)


class VersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Version

    min_version = factory.fuzzy.FuzzyDecimal(100)
    max_version = factory.LazyAttribute(lambda obj: obj.min_version + 1)
    name = factory.LazyAttribute(lambda obj: "Version %d" % obj.min_version)
    slug = factory.LazyAttribute(lambda obj: "v%d" % obj.min_version)
    visible = True
    default = factory.fuzzy.FuzzyChoice([False, True])
    product = factory.SubFactory(ProductFactory)
