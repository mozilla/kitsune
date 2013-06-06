import os

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files import File

from kitsune.gallery.forms import ImageForm, VideoForm
from kitsune.gallery.models import Image, Video
from kitsune.sumo.urlresolvers import reverse
from kitsune.upload.utils import _image_to_png, upload_media, check_file_size
from kitsune.upload.tasks import _scale_dimensions


def create_image(files, user):
    """Given an uploaded file, a user, and other data, it creates an Image"""
    up_file = files.values()[0]
    check_file_size(up_file, settings.IMAGE_MAX_FILESIZE)

    try:
        image = Image.objects.filter(creator=user, is_draft=True)
        # Delete other drafts, if any:
        image.exclude(pk=image[0].pk).delete()
        image = image[0]
    except IndexError:  # No drafts, create one
        image = Image(creator=user, is_draft=True)

    # Async uploads fallback to these defaults.
    image.title = get_draft_title(user)
    image.description = u'Autosaved draft.'
    image.locale = settings.WIKI_DEFAULT_LANGUAGE

    (up_file, is_animated) = _image_to_png(up_file)

    # Finally save the image along with uploading the file.
    image.file.save(up_file.name,
                    File(up_file), save=True)

    (width, height) = _scale_dimensions(image.file.width, image.file.height)
    delete_url = reverse('gallery.delete_media', args=['image', image.id])
    return {'name': up_file.name, 'url': image.get_absolute_url(),
            'thumbnail_url': image.thumbnail_url_if_set(),
            'width': width, 'height': height,
            'delete_url': delete_url}


def upload_image(request):
    """Uploads an image from the request."""
    return upload_media(request, ImageForm, create_image)


def create_video(files, user):
    """Given an uploaded file, a user, and other data, it creates a Video"""
    try:
        vid = Video.objects.filter(creator=user, is_draft=True)
        # Delete other drafts, if any:
        vid.exclude(pk=vid[0].pk).delete()
        vid = vid[0]
    except IndexError:  # No drafts, create one
        vid = Video(creator=user, is_draft=True)
    # Async uploads fallback to these defaults.
    vid.title = get_draft_title(user)
    vid.description = u'Autosaved draft.'
    vid.locale = settings.WIKI_DEFAULT_LANGUAGE

    for name in files:
        up_file = files[name]
        check_file_size(up_file, settings.VIDEO_MAX_FILESIZE)
        # name is in (webm, ogv, flv) sent from upload_video(), below
        getattr(vid, name).save(up_file.name, up_file, save=False)

        if 'thumbnail' == name:
            # Save poster too, we shrink it later.
            vid.poster.save(up_file.name, up_file, save=False)

    vid.save()
    if 'thumbnail' in files:
        thumb = vid.thumbnail
        (width, height) = _scale_dimensions(thumb.width, thumb.height)
    else:
        width = settings.THUMBNAIL_PROGRESS_WIDTH
        height = settings.THUMBNAIL_PROGRESS_HEIGHT
    delete_url = reverse('gallery.delete_media', args=['video', vid.id])
    return {'name': up_file.name, 'url': vid.get_absolute_url(),
            'thumbnail_url': vid.thumbnail_url_if_set(),
            'width': width,
            'height': height,
            'delete_url': delete_url}


def upload_video(request):
    """Uploads a video from the request; accepts multiple submitted formats"""
    return upload_media(request, VideoForm, create_video)


def check_media_permissions(media, user, perm_type):
    """Checks the permissions for user on media (image or video).

    Pass in: * media object (Image or Video)
             * (logged in) user
             * perm_type = 'delete', 'change', 'add'
    Raises PermissionDenied if not allowed. Owner is always allowed.

    """
    media_type = media.__class__.__name__.lower()
    perm_name = 'gallery.%s_%s' % (perm_type, media_type)
    if user != media.creator and not user.has_perm(perm_name):
        raise PermissionDenied


def get_draft_title(user):
    return u'Draft for user %s' % user.username
