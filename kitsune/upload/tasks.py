import logging
import os
import StringIO
import subprocess
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from celery import task
from PIL import Image

from kitsune.sumo.decorators import timeit


log = logging.getLogger("k.task")


@task(rate_limit="15/m")
@timeit
def generate_thumbnail(for_obj, from_field, to_field, max_size=settings.THUMBNAIL_SIZE):
    """Generate a thumbnail, given a model instance with from and to fields.

    Optionally specify a max_size.

    """
    from_ = getattr(for_obj, from_field)
    to_ = getattr(for_obj, to_field)

    # Bail silently if nothing to generate from, image was probably deleted.
    if not (from_ and default_storage.exists(from_.name)):
        log_msg = "No file to generate from: {model} {id}, {from_f} -> {to_f}"
        log.info(
            log_msg.format(
                model=for_obj.__class__.__name__,
                id=for_obj.id,
                from_f=from_field,
                to_f=to_field,
            )
        )
        return

    log_msg = "Generating thumbnail for {model} {id}: {from_f} -> {to_f}"
    log.info(
        log_msg.format(
            model=for_obj.__class__.__name__,
            id=for_obj.id,
            from_f=from_field,
            to_f=to_field,
        )
    )
    thumb_content = _create_image_thumbnail(from_.file, longest_side=max_size)
    if to_:  # Clean up old file before creating new one.
        to_.delete(save=False)
    # Don't modify the object.
    to_.save(from_.name, thumb_content, save=False)
    # Use update to avoid race conditions with updating different fields.
    # E.g. when generating two thumbnails for different fields of a single
    # object.
    for_obj.update(**{to_field: to_.name})


def _create_image_thumbnail(fileobj, longest_side=settings.THUMBNAIL_SIZE, pad=False):
    """
    Returns a thumbnail file with a set longest side.
    """
    original_image = Image.open(fileobj)
    original_image = original_image.convert("RGBA")
    file_width, file_height = original_image.size

    width, height = _scale_dimensions(file_width, file_height, longest_side)
    resized_image = original_image.resize((width, height), Image.ANTIALIAS)

    io = StringIO.StringIO()

    if pad:
        padded_image = _make_image_square(resized_image, longest_side)
        padded_image.save(io, "PNG")
    else:
        resized_image.save(io, "PNG")

    return ContentFile(io.getvalue())


def _make_image_square(source_image, side=settings.THUMBNAIL_SIZE):
    """Pads a rectangular image with transparency to make it square."""
    square_image = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    width = (side - source_image.size[0]) / 2
    height = (side - source_image.size[1]) / 2
    square_image.paste(source_image, (width, height))
    return square_image


def _scale_dimensions(width, height, longest_side=settings.THUMBNAIL_SIZE):
    """
    Returns a tuple (width, height), both smaller than longest side, and
    preserves scale.
    """

    if width < longest_side and height < longest_side:
        return (width, height)

    if width > height:
        new_width = longest_side
        new_height = (new_width * height) / width
        return (new_width, new_height)

    new_height = longest_side
    new_width = (new_height * width) / height
    return (new_width, new_height)


@task(rate_limit="15/m")
@timeit
def compress_image(for_obj, for_field):
    """Compress an image of given field for given object."""

    for_ = getattr(for_obj, for_field)

    # Bail silently if nothing to compress, image was probably deleted.
    if not (for_ and default_storage.exists(for_.name)):
        log_msg = "No file to compress for: {model} {id}, {for_f}"
        log.info(
            log_msg.format(
                model=for_obj.__class__.__name__, id=for_obj.id, for_f=for_field
            )
        )
        return

    # Bail silently if not a PNG.
    if not (os.path.splitext(for_.name)[1].lower() == ".png"):
        log_msg = "File is not PNG for: {model} {id}, {for_f}"
        log.info(
            log_msg.format(
                model=for_obj.__class__.__name__, id=for_obj.id, for_f=for_field
            )
        )
        return

    log_msg = "Compressing {model} {id}: {for_f}"
    log.info(
        log_msg.format(model=for_obj.__class__.__name__, id=for_obj.id, for_f=for_field)
    )

    _optipng(for_.name)


def _optipng(file_name):
    if not settings.OPTIPNG_PATH:
        return

    with default_storage.open(file_name, "rb") as file_obj:
        with NamedTemporaryFile(suffix=".png") as tmpfile:
            tmpfile.write(file_obj.read())
            subprocess.call(
                [settings.OPTIPNG_PATH, "-quiet", "-preserve", tmpfile.name]
            )
            file_content = ContentFile(tmpfile.read())
            default_storage.save(file_name, file_content)
