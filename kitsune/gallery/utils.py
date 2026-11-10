from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.utils import timezone
from django.utils.html import escape

from kitsune.gallery.forms import ImageForm
from kitsune.gallery.models import Image
from kitsune.gallery.storage import private_images_enabled
from kitsune.sumo.urlresolvers import reverse
from kitsune.upload.tasks import _scale_dimensions
from kitsune.upload.utils import _image_to_png, check_file_size, upload_media
from kitsune.wiki.managers import has_private_kb_access
from kitsune.wiki.models import Audience


def upload_knowledge_bases(user):
    """Private knowledge bases the user may upload to or pick from; None if public images only."""
    if not (private_images_enabled() and has_private_kb_access(user)):
        return None

    return list(Audience.objects.private_for(user).order_by("name"))


def can_upload_to(user, audience):
    """Whether the user may upload to, and finalize a draft in, the audience's knowledge base."""
    if audience.is_public:
        return True
    return private_images_enabled() and (
        Audience.objects.private_for(user).filter(pk=audience.pk).exists()
    )


def create_image(files, user, audience):
    """Saves the upload as the user's single draft, re-homed to the audience's knowledge base."""
    up_file = list(files.values())[0]
    check_file_size(up_file, settings.IMAGE_MAX_FILESIZE)
    (up_file, _is_animated) = _image_to_png(up_file)

    image = Image.objects.filter(creator=user, is_draft=True).first() or Image(
        creator=user, is_draft=True
    )
    old_files = [field_file.name for field_file in (image.file, image.thumbnail) if field_file]
    image.audience = audience
    image.thumbnail = None
    # Async uploads fallback to these defaults.
    image.title = get_draft_title(user)
    image.description = "Autosaved draft."
    image.locale = settings.WIKI_DEFAULT_LANGUAGE

    # Finally save the image along with uploading the file.
    image.file.save(up_file.name, File(up_file), save=True)
    for name in set(old_files) - {image.file.name}:
        image.file.storage.delete(name)

    name = escape(up_file.name)
    (width, height) = _scale_dimensions(image.file.width, image.file.height)
    delete_url = reverse("gallery.delete_media", args=[image.id])
    return {
        "name": name,
        "url": image.get_absolute_url(),
        "thumbnail_url": image.thumbnail_url_if_set(),
        "width": width,
        "height": height,
        "delete_url": delete_url,
    }


def upload_image(request, audience):
    """Uploads an image from the request into the audience's knowledge base."""
    return upload_media(request, ImageForm, create_image, audience=audience)


def check_media_permissions(media, user, perm_type):
    """Checks the permissions for user on media.

    Pass in: * media object (Image)
             * (logged in) user
             * perm_type = 'delete', 'change', 'add'
    Raises PermissionDenied if not allowed. Owner is always allowed.

    """
    media_type = media.__class__.__name__.lower()
    perm_name = "gallery.{}_{}".format(perm_type, media_type)
    if user != media.creator and not user.has_perm(perm_name):
        raise PermissionDenied


def get_draft_title(user):
    return "Draft for user {}. Created at: {}".format(user.username, timezone.now())
