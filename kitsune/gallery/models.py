from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone

from kitsune.gallery.storage import (
    PRIVATE_PREFIX,
    gallery_storage,
    image_upload_to,
    private_images_enabled,
    thumbnail_upload_to,
)
from kitsune.sumo.models import LocaleField, ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.config import DEFAULT_AUDIENCE_SLUG


class Media(ModelBase):
    """Generic model for media"""

    title = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)
    updated = models.DateTimeField(default=timezone.now, db_index=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="%(app_label)s_%(class)s_set"
    )
    description = models.TextField(max_length=10000)
    locale = LocaleField(default=settings.GALLERY_DEFAULT_LANGUAGE, db_index=True)
    is_draft = models.BooleanField(default=None, null=True, editable=False)

    class Meta:
        abstract = True
        ordering = ["-created"]
        unique_together = (("is_draft", "creator"),)

    def __str__(self):
        return "[{}] {}".format(self.locale, self.title)


class ImageManager(models.Manager):
    def public(self):
        """Images in a public knowledge base; draft filtering is the caller's."""
        return self.filter(audience__is_public=True)

    def in_default_kb(self):
        """The default knowledge base's images: the ones any markup may embed."""
        return self.filter(audience__slug=DEFAULT_AUDIENCE_SLUG)

    def private_in(self, audience):
        """The finalized images of a private knowledge base."""
        return self.filter(audience=audience, audience__is_public=False).exclude(is_draft=True)


class Image(Media):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gallery_images")
    audience = models.ForeignKey(
        "wiki.Audience", on_delete=models.PROTECT, editable=False, related_name="images"
    )
    file = models.ImageField(
        upload_to=image_upload_to,
        storage=gallery_storage,
        max_length=settings.MAX_FILEPATH_LENGTH,
        width_field="width",
        height_field="height",
    )
    thumbnail = models.ImageField(
        upload_to=thumbnail_upload_to,
        storage=gallery_storage,
        null=True,
        max_length=settings.MAX_FILEPATH_LENGTH,
    )
    height = models.IntegerField(null=True)
    width = models.IntegerField(null=True)

    objects = ImageManager()

    class Meta(Media.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["locale", "title", "audience"], name="gallery_image_locale_title_audience"
            )
        ]
        indexes = [
            models.Index(fields=["file"], name="gallery_image_file_idx"),
            models.Index(fields=["thumbnail"], name="gallery_image_thumbnail_idx"),
        ]

    def get_absolute_url(self):
        return reverse("gallery.media", args=[self.id])

    @property
    def is_private(self):
        return not self.audience.is_public

    def is_readable_by(self, user):
        """Private images need Staff, a member or the draft's creator; no query for public ones."""
        # Files under private/ stay private by name, whatever the knowledge base is now.
        if self.file.name.startswith(PRIVATE_PREFIX) and not private_images_enabled():
            return False

        if not self.is_private:
            return True

        # Fail closed: no private image is readable while private storage is off.
        if not (private_images_enabled() and user and user.is_authenticated):
            return False

        if self.is_draft and self.creator_id == user.pk:
            return True

        # Imported here to break the cycle wiki.models -> gallery.models.
        from kitsune.wiki.models import Audience

        return Audience.objects.private_for(user).filter(pk=self.audience_id).exists()

    def thumbnail_url_if_set(self):
        """Returns self.thumbnail, if set, else self.file"""
        return self.thumbnail.url if self.thumbnail else self.file.url

    def documents(self, user=None):
        """Get the documents visible to the given user that include this image."""
        from kitsune.wiki.models import Document

        return Document.objects.visible(user, documentimage__image=self)


@receiver(pre_delete, sender=Image)
def delete_image_files(sender, instance, **kwargs):
    """Public files go with the row, as for every model; private ones once the delete commits."""
    for field_file in (instance.file, instance.thumbnail):
        if not field_file:
            continue

        if field_file.name.startswith(PRIVATE_PREFIX):
            # The defaults bind this iteration's file; a closure would see only the last one.
            transaction.on_commit(
                lambda storage=field_file.storage, name=field_file.name: storage.delete(name),
                using=kwargs["using"],
                robust=True,
            )
        else:
            field_file.delete()
