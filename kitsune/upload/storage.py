import hashlib
import itertools
import os
import time

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


DjangoStorage = S3Boto3Storage if settings.AWS_ACCESS_KEY_ID else FileSystemStorage


class RenameFileStorage(DjangoStorage):
    """Subclass Django's file system storage to add our file naming
    conventions."""

    def get_available_name(self, name, max_length=None):
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)

        # Set file_root to something we like: clean and all ascii
        md5_sub = hashlib.md5(file_root.encode("utf8")).hexdigest()[0:6]
        file_root = time.strftime("%Y-%m-%d-%H-%M-%S-", time.localtime()) + md5_sub
        name = os.path.join(dir_name, file_root + file_ext)

        # If the filename already exists, add an underscore and a number
        # (before the file extension, if one exists) to the filename until
        # the generated filename doesn't exist.
        count = itertools.count(1)
        while self.exists(name):
            # file_ext includes the dot.
            name = os.path.join(dir_name, "%s_%s%s" % (file_root, next(count), file_ext))

        return name
