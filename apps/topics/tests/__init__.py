# -*- coding: utf-8 -*-
from datetime import datetime

from django.template.defaultfilters import slugify

from sumo.tests import with_save
from topics.models import Topic


# Model makers.

@with_save
def topic(**kwargs):
    """Return a topic with enough stuff filled out that it can be saved."""
    defaults = {'title': u'đ' + str(datetime.now()),
                'display_order': 1,
                'visible': True}
    defaults.update(kwargs)
    if 'slug' not in kwargs:
        defaults['slug'] = slugify(defaults['title'])
    return Topic(**defaults)
