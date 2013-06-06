import os

from django.conf import settings
from django.db import models

from kitsune.sumo.models import ModelBase


class Product(ModelBase):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField(upload_to=settings.PRODUCT_IMAGE_PATH, null=True,
                              blank=True,
                              max_length=settings.MAX_FILEPATH_LENGTH)

    # Dictates the order in which products are displayed in product
    # lists.
    display_order = models.IntegerField()

    # Whether or not this product is visible in the ui to users.
    visible = models.BooleanField(default=False)

    class Meta(object):
        ordering = ['display_order']

    def __unicode__(self):
        return u'%s' % self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return os.path.join(
            settings.STATIC_URL, 'img', 'product_placeholder.png')
