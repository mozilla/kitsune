import functools
import logging
import posixpath

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage, default_storage
from django.utils.encoding import filepath_to_uri

from kitsune.upload.storage import PrivateFileSystemStorage, PrivateGoogleCloudStorage

log = logging.getLogger("k.gallery")

PRIVATE_PREFIX = "private/"
PRIVATE_MEDIA_URL = "/private-media/"
# Blobs above this spool to disk; django-storages' default, 0, buffers whole files in memory.
GCS_MAX_MEMORY_SIZE = 1024 * 1024


@functools.cache
def build_private_storage(gs_bucket_name, gs_private_bucket_name, uses_s3, root):
    # Cached on the settings it reads: one GCS client per bucket, and overrides in tests apply.
    if gs_bucket_name:
        # The same bucket would put private files behind the public CDN.
        if not gs_private_bucket_name or gs_private_bucket_name == gs_bucket_name:
            return None
        # Passed explicitly: the GS_* defaults are the public bucket's (CDN endpoint, public ACL).
        return PrivateGoogleCloudStorage(
            bucket_name=gs_private_bucket_name,
            custom_endpoint=None,
            default_acl=None,
            object_parameters={},
            max_memory_size=GCS_MAX_MEMORY_SIZE,
        )

    if uses_s3:
        return None

    return PrivateFileSystemStorage(location=root)


def private_storage():
    """The storage for private files, or None when private uploads are off."""
    return build_private_storage(
        settings.GS_BUCKET_NAME,
        settings.GS_PRIVATE_BUCKET_NAME,
        bool(settings.AWS_ACCESS_KEY_ID),
        str(settings.PRIVATE_MEDIA_ROOT),
    )


def private_images_enabled():
    return private_storage() is not None


class GalleryStorage(Storage):
    """Names under PRIVATE_PREFIX go to the private storage, everything else to the default one."""

    def backend(self, name):
        if not name.startswith(PRIVATE_PREFIX):
            return default_storage

        storage = private_storage()
        if storage is None:
            raise ImproperlyConfigured("Private images need a private storage backend.")

        return storage

    def open(self, name, mode="rb"):
        return self.backend(name).open(name, mode)

    def save(self, name, content, max_length=None):
        return self.backend(name).save(name, content, max_length=max_length)

    def delete(self, name):
        if name.startswith(PRIVATE_PREFIX) and not private_images_enabled():
            log.warning(f"Private storage is off; {name} was not deleted.")
            return

        self.backend(name).delete(name)

    def exists(self, name):
        return self.backend(name).exists(name)

    def size(self, name):
        return self.backend(name).size(name)

    def path(self, name):
        return self.backend(name).path(name)

    def url(self, name):
        if name.startswith(PRIVATE_PREFIX):
            return PRIVATE_MEDIA_URL + filepath_to_uri(name)

        return default_storage.url(name)


def gallery_storage():
    return GalleryStorage()


def upload_path(directory, filename, private):
    prefix = PRIVATE_PREFIX if private else ""
    return prefix + posixpath.join(directory, filename.removeprefix(PRIVATE_PREFIX))


def image_upload_to(instance, filename):
    return upload_path(settings.GALLERY_IMAGE_PATH, filename, private=instance.is_private)


def thumbnail_upload_to(instance, filename):
    # Named from its source's full name, so a private source's prefix moves to the front.
    return upload_path(
        settings.GALLERY_IMAGE_THUMBNAIL_PATH,
        filename,
        private=filename.startswith(PRIVATE_PREFIX),
    )
