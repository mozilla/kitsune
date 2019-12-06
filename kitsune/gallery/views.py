import imghdr
import json
import logging

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from kitsune.access.decorators import login_required
from kitsune.gallery import ITEMS_PER_PAGE
from kitsune.gallery.forms import ImageForm
from kitsune.gallery.models import Image, Video
from kitsune.gallery.utils import upload_image, check_media_permissions
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import paginate
from kitsune.upload.tasks import compress_image, generate_thumbnail
from kitsune.upload.utils import FileTooLargeError
from kitsune.wiki.tasks import schedule_rebuild_kb


log = logging.getLogger('k.gallery')


def gallery(request, media_type='image'):
    """The media gallery.

    Filter can be set to 'images' or 'videos'.

    """
    if media_type == 'image':
        media_qs = Image.objects.filter(locale=request.LANGUAGE_CODE)
    elif media_type == 'video':
        media_qs = Video.objects.filter(locale=request.LANGUAGE_CODE)
    else:
        raise Http404

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    drafts = _get_drafts(request.user)
    image = drafts['image'][0] if drafts['image'] else None
    image_form = _init_media_form(ImageForm, request, image)
    if request.method == 'POST':
        image_form.is_valid()

    return render(request, 'gallery/gallery.html', {
        'media': media,
        'media_type': media_type,
        'image_form': image_form,
        'submitted': request.method == 'POST'})


@login_required
@require_POST
def upload(request, media_type='image'):
    """Finalizes an uploaded draft."""
    drafts = _get_drafts(request.user)
    if media_type == 'image' and drafts['image']:
        # We're publishing an image draft!
        image_form = _init_media_form(ImageForm, request, drafts['image'][0])
        if image_form.is_valid():
            img = image_form.save(is_draft=None)
            generate_thumbnail.delay(img, 'file', 'thumbnail')
            compress_image.delay(img, 'file')
            # Rebuild KB
            schedule_rebuild_kb()
            return HttpResponseRedirect(img.get_absolute_url())
        else:
            return gallery(request, media_type='image')

    return HttpResponseBadRequest('Unrecognized POST request.')


@login_required
@require_POST
def cancel_draft(request, media_type='image'):
    """Delete an existing draft for the user."""
    drafts = _get_drafts(request.user)
    if media_type == 'image' and drafts['image']:
        drafts['image'].delete()
        drafts['image'] = None
    else:
        msg = _('Unrecognized request or nothing to cancel.')
        content_type = None
        if request.is_ajax():
            msg = json.dumps({'status': 'error', 'message': msg})
            content_type = 'application/json'
        return HttpResponseBadRequest(msg, content_type=content_type)

    if request.is_ajax():
        return HttpResponse(json.dumps({'status': 'success'}),
                            content_type='application/json')

    return HttpResponseRedirect(reverse('gallery.gallery', args=[media_type]))


def gallery_async(request):
    """AJAX endpoint to media gallery.

    Returns an HTML list representation of the media.

    """
    # Maybe refactor this into existing views and check request.is_ajax?
    media_type = request.GET.get('type', 'image')
    term = request.GET.get('q')
    media_locale = request.GET.get('locale', settings.WIKI_DEFAULT_LANGUAGE)
    if media_type == 'image':
        media_qs = Image.objects
    elif media_type == 'video':
        media_qs = Video.objects
    else:
        raise Http404

    media_qs = media_qs.filter(locale=media_locale)

    if term:
        media_qs = media_qs.filter(Q(title__icontains=term) |
                                   Q(description__icontains=term))

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    return render(request, 'gallery/includes/media_list.html', {
        'media_list': media})


def search(request, media_type):
    """Search the media gallery."""

    term = request.GET.get('q')
    if not term:
        url = reverse('gallery.gallery', args=[media_type])
        return HttpResponseRedirect(url)

    filter = Q(title__icontains=term) | Q(description__icontains=term)

    if media_type == 'image':
        media_qs = Image.objects.filter(filter, locale=request.LANGUAGE_CODE)
    elif media_type == 'video':
        media_qs = Video.objects.filter(filter, locale=request.LANGUAGE_CODE)
    else:
        raise Http404

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    return render(request, 'gallery/search.html', {
        'media': media,
        'media_type': media_type,
        'q': term})


@login_required
def delete_media(request, media_id, media_type='image'):
    """Delete media and redirect to gallery view."""
    media, media_format = _get_media_info(media_id, media_type)

    check_media_permissions(media, request.user, 'delete')

    if request.method == 'GET':
        # Render the confirmation page
        return render(request, 'gallery/confirm_media_delete.html', {
            'media': media,
            'media_type': media_type,
            'media_format': media_format})

    # Handle confirm delete form POST
    log.warning('User %s is deleting %s with id=%s' %
                (request.user, media_type, media.id))
    media.delete()
    # Rebuild KB
    schedule_rebuild_kb()
    return HttpResponseRedirect(reverse('gallery.gallery', args=[media_type]))


@login_required
def edit_media(request, media_id, media_type='image'):
    """Edit media means only changing the description, for now."""
    media, media_format = _get_media_info(media_id, media_type)

    check_media_permissions(media, request.user, 'change')

    if media_type == 'image':
        media_form = _init_media_form(ImageForm, request, media,
                                      ('locale', 'title'))
    else:
        raise Http404

    if request.method == 'POST' and media_form.is_valid():
        media = media_form.save(update_user=request.user, is_draft=False)
        return HttpResponseRedirect(
            reverse('gallery.media', args=[media_type, media_id]))

    return render(request, 'gallery/edit_media.html', {
        'media': media,
        'media_format': media_format,
        'form': media_form,
        'media_type': media_type})


def media(request, media_id, media_type='image'):
    """The media page."""
    media, media_format = _get_media_info(media_id, media_type)
    return render(request, 'gallery/media.html', {
        'media': media,
        'media_format': media_format,
        'media_type': media_type})


@login_required
@require_POST
@xframe_options_sameorigin
def upload_async(request, media_type='image'):
    """Upload images or videos from request.FILES."""
    # TODO(paul): validate the Submit File on upload modal async
    #             even better, use JS validation for title length.
    try:
        if media_type == 'image':
            file_info = upload_image(request)
        else:
            msg = _('Unrecognized media type.')
            return HttpResponseBadRequest(
                json.dumps({'status': 'error', 'message': msg}))
    except FileTooLargeError as e:
        return HttpResponseBadRequest(
            json.dumps({'status': 'error', 'message': e.args[0]}))

    if isinstance(file_info, dict) and 'thumbnail_url' in file_info:
        schedule_rebuild_kb()
        return HttpResponse(
            json.dumps({'status': 'success', 'file': file_info}))

    message = _('Could not upload your image.')
    return HttpResponseBadRequest(
        json.dumps({'status': 'error',
                    'message': str(message),
                    'errors': file_info}))


def _get_media_info(media_id, media_type):
    """Returns an image or video along with media format for the image."""
    media_format = None
    if media_type == 'image':
        media = get_object_or_404(Image, pk=media_id)
        try:
            media_format = imghdr.what(media.file.file)
        except UnicodeEncodeError:
            pass
    elif media_type == 'video':
        media = get_object_or_404(Video, pk=media_id)
    else:
        raise Http404
    return (media, media_format)


def _get_drafts(user):
    """Get video and image drafts for a given user."""
    drafts = {'image': None, 'video': None}
    if user.is_authenticated():
        drafts['image'] = Image.objects.filter(creator=user, is_draft=True)
        drafts['video'] = Video.objects.filter(creator=user, is_draft=True)
    return drafts


def _init_media_form(form_cls, request=None, obj=None,
                     ignore_fields=()):
    """Initializes the media form with an Image/Video instance and POSTed data.

    form_cls is a django ModelForm
    Request method must be POST for POST data to be bound.
    exclude_fields contains the list of fields to default to their current
    value from the Image/Video object.

    """
    post_data = None
    initial = None
    if request:
        initial = {'locale': request.LANGUAGE_CODE}
    file_data = None
    if request.method == 'POST':
        file_data = request.FILES
        post_data = request.POST.copy()
        if obj and ignore_fields:
            for f in ignore_fields:
                post_data[f] = getattr(obj, f)

    return form_cls(post_data, file_data, instance=obj, initial=initial,
                    is_ajax=False)
