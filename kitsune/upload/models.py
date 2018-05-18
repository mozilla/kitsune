from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from kitsune.sumo.templatetags.jinja_helpers import reverse
from kitsune.sumo.models import ModelBase
from kitsune.sumo.utils import auto_delete_files


@auto_delete_files
class ImageAttachment(ModelBase):
    """An image attached to an object using a generic foreign key"""
    file = models.ImageField(upload_to=settings.IMAGE_UPLOAD_PATH,
                             max_length=settings.MAX_FILEPATH_LENGTH)
    thumbnail = models.ImageField(upload_to=settings.THUMBNAIL_UPLOAD_PATH,
                                  null=True)
    creator = models.ForeignKey(User, related_name='image_attachments')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    content_object = generic.GenericForeignKey()

    def __unicode__(self):
        return self.file.name

    def get_absolute_url(self):
        return self.file.url

    def thumbnail_if_set(self):
        """Returns self.thumbnail, if set, else self.file"""
        return self.thumbnail if self.thumbnail else self.file

    def get_delete_url(self):
        """Returns the URL to delete this object. Assumes the object has an
        id."""
        return reverse('upload.del_image_async', args=[self.id])
