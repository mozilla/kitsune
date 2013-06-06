# -*- coding: utf-8 -*-
from datetime import datetime

from django.template.defaultfilters import slugify

from kitsune.products.models import Product
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
