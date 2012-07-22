import os

from django.conf import settings
from django.db import models

from sumo.models import ModelBase


class Product(ModelBase):
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()

    # Dictates the order in which products are displayed in product
    # lists.
    display_order = models.IntegerField()

    # Whether or not this product is visible in the ui to users.
    visible = models.BooleanField(default=False)

    slug = models.SlugField()

    class Meta(object):
        ordering = ['display_order']

    def __unicode__(self):
        return u'%s' % self.title

    @property
    def image_url(self):
        return os.path.join(
            settings.STATIC_URL, 'img', 'products', self.slug + '.png')
