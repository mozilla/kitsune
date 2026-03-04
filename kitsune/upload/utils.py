import io
import os

from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _lazy
from PIL import Image

from kitsune.upload.forms import ImageAttachmentUploadForm
from kitsune.upload.models import ImageAttachment
from kitsune.upload.tasks import _scale_dimensions, compress_image, generate_thumbnail


class FileTooLargeError(Exception):
    pass


def open_as_pil_image(fileobj):
    """Open fileobj as a PIL image, raising FileTooLargeError if dimensions exceed IMAGE_MAX_PIXELS."""
    msg = _lazy("Image exceeds the maximum allowed size of %d megapixels.") % (
        settings.IMAGE_MAX_PIXELS // 1_000_000,
    )
    try:
        image = Image.open(fileobj)
    except Image.DecompressionBombError:
        raise FileTooLargeError(msg)

    if image.width * image.height > settings.IMAGE_MAX_PIXELS:
        raise FileTooLargeError(msg)

    return image


def check_file_size(f, max_allowed_size):
    """Check the file size of f is less than max_allowed_size

    Raise FileTooLargeError if the check fails.

    """
    if f.size > max_allowed_size:
        message = _lazy('"%s" is too large (%sKB), the limit is %sKB') % (
            f.name,
            f.size >> 10,
            max_allowed_size >> 10,
        )
        raise FileTooLargeError(message)


def create_imageattachment(files, user, obj):
    """
    Given an uploaded file, a user and an object, it creates an ImageAttachment
    owned by `user` and attached to `obj`.
    """
    up_file = files["image"]
    check_file_size(up_file, settings.IMAGE_MAX_FILESIZE)

    (up_file, is_animated) = _image_to_png(up_file)

    image = ImageAttachment(content_object=obj, creator=user)
    image.file.save(up_file.name, File(up_file), save=True)

    # Compress and generate thumbnail off thread
    generate_thumbnail.delay("upload.ImageAttachment", image.id, "file", "thumbnail")
    if not is_animated:
        compress_image.delay("upload.ImageAttachment", image.id, "file")

    # Refresh because the image may have been changed by tasks.
    image.refresh_from_db()

    (width, height) = _scale_dimensions(image.file.width, image.file.height)

    # The filename may contain html in it. Escape it.
    name = escape(up_file.name)

    return {
        "name": name,
        "url": image.file.url,
        "thumbnail_url": image.thumbnail_if_set().url,
        "width": width,
        "height": height,
        "delete_url": image.get_delete_url(),
    }


def _image_to_png(up_file):
    with open_as_pil_image(up_file) as image:
        # This approach is recommended by pillow for checking if an image is animated.
        is_animated = getattr(image, "is_animated", False)

        if is_animated:
            up_file.name = os.path.splitext(up_file.name)[0] + ".gif"
        else:
            options = {}
            if "transparency" in image.info:
                options["transparency"] = image.info["transparency"]

            png_image = io.BytesIO()
            image.save(png_image, format="PNG", **options)

            up_file = InMemoryUploadedFile(
                png_image,
                None,
                os.path.splitext(up_file.name)[0] + ".png",
                "image/png",
                len(png_image.getbuffer()),
                None,
            )

    return (up_file, is_animated)


def _make_image_square(source_image, side=settings.THUMBNAIL_SIZE):
    """Pads a rectangular image with transparency to make it square."""
    square_image = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    width = (side - source_image.size[0]) // 2
    height = (side - source_image.size[1]) // 2
    square_image.paste(source_image, (width, height))
    return square_image


def create_image_thumbnail(fileobj, longest_side=settings.THUMBNAIL_SIZE, pad=False):
    """
    Returns a thumbnail file with a set longest side.
    """
    original_image = open_as_pil_image(fileobj)
    original_image = original_image.convert("RGBA")
    file_width, file_height = original_image.size

    width, height = _scale_dimensions(file_width, file_height, longest_side)
    resized_image = original_image.resize((width, height), Image.LANCZOS)

    data = io.BytesIO()

    if pad:
        padded_image = _make_image_square(resized_image, longest_side)
        padded_image.save(data, "PNG")
    else:
        resized_image.save(data, "PNG")

    return ContentFile(data.getvalue())


def upload_imageattachment(request, obj):
    """Uploads image attachments. See upload_media.

    Attaches images to the given object, using the create_imageattachment
    callback.

    """
    return upload_media(request, ImageAttachmentUploadForm, create_imageattachment, obj=obj)


def upload_media(request, form_cls, up_file_callback, instance=None, **kwargs):
    """
    Uploads media files and returns a list with information about each media:
    name, url, thumbnail_url, width, height.

    Args:
    * request object
    * form class, used to instantiate and validate form for upload
    * callback to save the file given its content and creator
    * extra kwargs will all be passed to the callback

    """
    form = form_cls(request.POST, request.FILES)
    if request.method == "POST" and form.is_valid():
        return up_file_callback(request.FILES, request.user, **kwargs)
    elif not form.is_valid():
        return form.errors
    return None
