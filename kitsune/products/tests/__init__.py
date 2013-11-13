# -*- coding: utf-8 -*-
from datetime import datetime
from random import randint

from django.template.defaultfilters import slugify

from kitsune.products.models import Product, Topic, Version
from kitsune.sumo.tests import with_save


@with_save
def product(**kwargs):
    """Create and return a product."""
    defaults = {'title': u'đ' + str(datetime.now()),
                'display_order': 1,
                'visible': True}
    defaults.update(kwargs)

    if 'slug' not in kwargs:
        defaults['slug'] = slugify(defaults['title'])

    return Product(**defaults)


@with_save
def topic(**kwargs):
    """Create and return a topic."""
    defaults = {'title': u'đ' + str(datetime.now()),
                'display_order': 1,
                'visible': True}
    defaults.update(kwargs)

    if 'slug' not in kwargs:
        defaults['slug'] = slugify(defaults['title'])

    if 'product' not in kwargs:
        defaults['product'] = product(save=True)

    return Topic(**defaults)


@with_save
def version(**kwargs):
    """Create and return a version."""
    v = randint(0, 1000)

    defaults = {
        'name': 'Version %d.0' % v,
        'slug': 'v%d' % v,
        'min_version': v,
        'max_version': v + 1,
        'visible': True,
        'default': False,
    }
    defaults.update(kwargs)

    if 'product' not in kwargs:
        defaults['product'] = product(save=True)

    return Version(**defaults)


@with_save
def platform(**kwargs):
    """Create and return a platform."""
    v = randint(0, 1000)

    defaults = {
        'name': 'Platform %d' % v,
        'slug': 'platform%d' % v,
        'visible': True,
        'display_order': 0,
    }
    defaults.update(kwargs)

    return Version(**defaults)
