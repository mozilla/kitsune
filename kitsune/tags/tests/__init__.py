from datetime import datetime

from django.template.defaultfilters import slugify

from taggit.models import Tag

from kitsune.sumo.tests import with_save


@with_save
def tag(**kwargs):
    """Model Maker for Tags."""
    defaults = {'name': str(datetime.now())}
    defaults.update(kwargs)
    if 'slug' not in kwargs:
        defaults['slug'] = slugify(defaults['title'])
    return Tag(**defaults)
