from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from kitsune.sumo.models import ModelBase, LocaleField
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import auto_delete_files


class Media(ModelBase):
    """Generic model for media"""
    title = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    updated = models.DateTimeField(default=datetime.now, db_index=True)
    updated_by = models.ForeignKey(User, null=True)
    description = models.TextField(max_length=10000)
    locale = LocaleField(default=settings.GALLERY_DEFAULT_LANGUAGE,
                         db_index=True)
    is_draft = models.NullBooleanField(default=None, null=True, editable=False)

    class Meta(object):
        abstract = True
        ordering = ['-created']
        unique_together = (('locale', 'title'), ('is_draft', 'creator'))

    def __unicode__(self):
        return '[%s] %s' % (self.locale, self.title)


@auto_delete_files
class Image(Media):
    creator = models.ForeignKey(User, related_name='gallery_images')
    file = models.ImageField(upload_to=settings.GALLERY_IMAGE_PATH,
                             max_length=settings.MAX_FILEPATH_LENGTH,
                             width_field='width',
                             height_field='height')
    thumbnail = models.ImageField(
        upload_to=settings.GALLERY_IMAGE_THUMBNAIL_PATH, null=True,
        max_length=settings.MAX_FILEPATH_LENGTH)
    height = models.IntegerField(null=True)
    width = models.IntegerField(null=True)

    def get_absolute_url(self):
        return reverse('gallery.media', args=['image', self.id])

    def thumbnail_url_if_set(self):
        """Returns self.thumbnail, if set, else self.file"""
        return self.thumbnail.url if self.thumbnail else self.file.url

    @property
    def documents(self):
        """Get the documents that include this image."""
        from kitsune.wiki.models import Document
        return Document.objects.filter(documentimage__image=self)


@auto_delete_files
class Video(Media):
    creator = models.ForeignKey(User, related_name='gallery_videos')
    webm = models.FileField(upload_to=settings.GALLERY_VIDEO_PATH, null=True,
                            max_length=settings.MAX_FILEPATH_LENGTH)
    ogv = models.FileField(upload_to=settings.GALLERY_VIDEO_PATH, null=True,
                           max_length=settings.MAX_FILEPATH_LENGTH)
    flv = models.FileField(upload_to=settings.GALLERY_VIDEO_PATH, null=True,
                           max_length=settings.MAX_FILEPATH_LENGTH)
    poster = models.ImageField(upload_to=settings.GALLERY_VIDEO_THUMBNAIL_PATH,
                               max_length=settings.MAX_FILEPATH_LENGTH,
                               null=True)
    thumbnail = models.ImageField(
        upload_to=settings.GALLERY_VIDEO_THUMBNAIL_PATH, null=True,
        max_length=settings.MAX_FILEPATH_LENGTH)

    def get_absolute_url(self):
        return reverse('gallery.media', args=['video', self.id])

    def thumbnail_url_if_set(self):
        """Returns self.thumbnail.url, if set, else default thumbnail URL"""
        progress_url = settings.GALLERY_VIDEO_THUMBNAIL_PROGRESS_URL
        return self.thumbnail.url if self.thumbnail else progress_url
