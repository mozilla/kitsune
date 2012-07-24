from django.conf import settings
from django.db import models

from sumo.models import ModelBase


class Topic(ModelBase):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField(upload_to=settings.TOPIC_IMAGE_PATH, null=True,
                              blank=True,
                              max_length=settings.MAX_FILEPATH_LENGTH)

    # Topics can optionally have a parent.
    parent = models.ForeignKey('self', related_name='subtopics',
                               null=True, blank=True)

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
        return self.image.url
