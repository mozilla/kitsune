import logging
import os
import StringIO
import subprocess

from django.conf import settings
from django.core.files.base import ContentFile

from celery.task import task
from PIL import Image

log = logging.getLogger('k.task')


@task(rate_limit='15/m')
def generate_thumbnail(for_obj, from_field, to_field,
                       max_size=settings.THUMBNAIL_SIZE):
    """Generate a thumbnail, given a model instance with from and to fields.

    Optionally specify a max_size.

    """
    from_ = getattr(for_obj, from_field)
    to_ = getattr(for_obj, to_field)

    # Bail silently if nothing to generate from, image was probably deleted.
    if not (from_ and os.path.isfile(from_.path)):
        log_msg = 'No file to generate from: {model} {id}, {from_f} -> {to_f}'
        log.info(log_msg.format(model=for_obj.__class__.__name__,
                                id=for_obj.id, from_f=from_field,
                                to_f=to_field))
        return

    log_msg = 'Generating thumbnail for {model} {id}: {from_f} -> {to_f}'
    log.info(log_msg.format(model=for_obj.__class__.__name__, id=for_obj.id,
                            from_f=from_field, to_f=to_field))
    thumb_content = _create_image_thumbnail(from_.path, longest_side=max_size)
    file_path = from_.path
    if to_:  # Clean up old file before creating new one.
        to_.delete(save=False)
    # Don't modify the object.
    to_.save(file_path, thumb_content, save=False)
    # Use update to avoid race conditions with updating different fields.
    # E.g. when generating two thumbnails for different fields of a single
    # object.
    for_obj.update(**{to_field: to_.name})


def _create_image_thumbnail(file_path, longest_side=settings.THUMBNAIL_SIZE,
                            pad=False):
    """
    Returns a thumbnail file with a set longest side.
    """
    original_image = Image.open(file_path)
    original_image = original_image.convert('RGBA')
    file_width, file_height = original_image.size

    width, height = _scale_dimensions(file_width, file_height, longest_side)
    resized_image = original_image.resize((width, height), Image.ANTIALIAS)

    io = StringIO.StringIO()

    if pad:
        padded_image = _make_image_square(resized_image, longest_side)
        padded_image.save(io, 'PNG')
    else:
        resized_image.save(io, 'PNG')

    return ContentFile(io.getvalue())


def _make_image_square(source_image, side=settings.THUMBNAIL_SIZE):
    """Pads a rectangular image with transparency to make it square."""
    square_image = Image.new('RGBA', (side, side), (255, 255, 255, 0))
    square_image.paste(source_image,
                      ((side - source_image.size[0]) / 2,
                       (side - source_image.size[1]) / 2))
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


@task(rate_limit='15/m')
def compress_image(for_obj, for_field):
    """Compress an image of given field for given object."""

    for_ = getattr(for_obj, for_field)

    # Bail silently if nothing to compress, image was probably deleted.
    if not (for_ and os.path.isfile(for_.path)):
        log_msg = 'No file to compress for: {model} {id}, {for_f}'
        log.info(log_msg.format(model=for_obj.__class__.__name__,
                                id=for_obj.id, for_f=for_field))
        return

    # Bail silently if not a PNG.
    if not (os.path.splitext(for_.path)[1].lower() == '.png'):
        log_msg = 'File is not PNG for: {model} {id}, {for_f}'
        log.info(log_msg.format(model=for_obj.__class__.__name__,
                                id=for_obj.id, for_f=for_field))
        return

    log_msg = 'Compressing {model} {id}: {for_f}'
    log.info(log_msg.format(model=for_obj.__class__.__name__, id=for_obj.id,
                            for_f=for_field))

    file_path = for_.path
    if settings.OPTIPNG_PATH is not None:
        subprocess.call([settings.OPTIPNG_PATH,
                         '-quiet', '-preserve', file_path])
