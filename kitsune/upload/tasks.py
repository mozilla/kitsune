import logging
import os
import subprocess
from tempfile import NamedTemporaryFile

from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

log = logging.getLogger("k.task")


@shared_task(rate_limit="15/m")
def generate_thumbnail(
    obj_model_name, obj_id, from_field, to_field, max_size=settings.THUMBNAIL_SIZE
):
    """
    Generate a thumbnail, given an object's model name, id, "from" and "to" fields, and
    optionally the "max_size" of its longest side. The model name must be in the form of
    "<app>.<model-name>", so for example, "gallery.Image" or "upload.ImageAttachment".
    """
    from kitsune.upload.utils import create_image_thumbnail

    # Get the model of the object, and then get the object itself.
    model = apps.get_model(obj_model_name)
    obj = model.objects.get(id=obj_id)

    from_ = getattr(obj, from_field)
    to_ = getattr(obj, to_field)

    # Bail silently if nothing to generate from. The image was probably deleted.
    if not (from_ and default_storage.exists(from_.name)):
        log.info(
            f"No file to generate from: {obj_model_name} {obj.id}, {from_field} -> {to_field}"
        )
        return

    log.info(f"Generating thumbnail for {obj_model_name} {obj.id}: {from_field} -> {to_field}")
    thumb_content = create_image_thumbnail(from_.file, longest_side=max_size)
    if to_:
        # Clean up old file before creating new one.
        to_.delete(save=False)
    # Don't modify the object.
    to_.save(from_.name, thumb_content, save=False)
    # Use update to avoid race conditions with updating different fields.
    # E.g. when generating two thumbnails for different fields of a single
    # object.
    obj.update(**{to_field: to_.name})


def _scale_dimensions(width, height, longest_side=settings.THUMBNAIL_SIZE):
    """
    Returns a tuple (width, height), both smaller than longest side, and
    preserves scale.
    """

    if width < longest_side and height < longest_side:
        return (width, height)

    if width > height:
        new_width = longest_side
        new_height = (new_width * height) // width
        return (new_width, new_height)

    new_height = longest_side
    new_width = (new_height * width) // height
    return (new_width, new_height)


@shared_task(rate_limit="15/m")
def compress_image(obj_model_name, obj_id, for_field):
    """Compress an image of given field for given object."""

    # Get the model of the object, and then get the object itself.
    model = apps.get_model(obj_model_name)
    obj = model.objects.get(id=obj_id)

    for_ = getattr(obj, for_field)

    # Bail silently if nothing to compress. The image was probably deleted.
    if not (for_ and default_storage.exists(for_.name)):
        log.info(f"No file to compress for: {obj_model_name} {obj.id}, {for_field}")
        return

    # Bail silently if not a PNG.
    if not (os.path.splitext(for_.name)[1].lower() == ".png"):
        log.info(f"File is not PNG for: {obj_model_name} {obj.id}, {for_field}")
        return

    log.info(f"Compressing {obj_model_name} {obj.id}: {for_field}")
    _optipng(for_.name)


def _optipng(file_name):
    if not settings.OPTIPNG_PATH:
        return

    with default_storage.open(file_name, "rb") as file_obj:
        with NamedTemporaryFile(suffix=".png") as tmpfile:
            tmpfile.write(file_obj.read())
            subprocess.call([settings.OPTIPNG_PATH, "-quiet", "-preserve", tmpfile.name])
            file_content = ContentFile(tmpfile.read())
            default_storage.save(file_name, file_content)
