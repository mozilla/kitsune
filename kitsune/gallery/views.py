import json
import logging

from django.conf import settings
from django.db.models import Q
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST
from PIL import Image as PILImage
from PIL import UnidentifiedImageError

from kitsune.access.decorators import login_required
from kitsune.gallery import ITEMS_PER_PAGE
from kitsune.gallery.forms import ImageForm
from kitsune.gallery.models import Image
from kitsune.gallery.utils import check_media_permissions, upload_image
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import paginate
from kitsune.upload.tasks import compress_image, generate_thumbnail
from kitsune.upload.utils import FileTooLargeError
from kitsune.wiki.tasks import schedule_rebuild_kb

log = logging.getLogger("k.gallery")


def gallery(request):
    """The media gallery."""
    media_qs = Image.objects.filter(locale=request.LANGUAGE_CODE)
    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    drafts = _get_drafts(request.user)
    image = drafts[0] if drafts else None
    image_form = _init_media_form(ImageForm, request, image)
    if request.method == "POST":
        image_form.is_valid()

    return render(
        request,
        "gallery/gallery.html",
        {
            "media": media,
            "image_form": image_form,
            "submitted": request.method == "POST",
            "locale": request.LANGUAGE_CODE,
        },
    )


@login_required
@require_POST
def upload(request):
    """Finalizes an uploaded draft."""
    drafts = _get_drafts(request.user)
    if drafts:
        # We're publishing an image draft!
        image_form = _init_media_form(ImageForm, request, drafts[0])
        if image_form.is_valid():
            img = image_form.save(is_draft=None)
            generate_thumbnail.delay("gallery.Image", img.id, "file", "thumbnail")
            compress_image.delay("gallery.Image", img.id, "file")
            # Rebuild KB
            schedule_rebuild_kb()
            return HttpResponseRedirect(img.get_absolute_url())
        else:
            return gallery(request)

    return HttpResponseBadRequest("Unrecognized POST request.")


@login_required
@require_POST
def cancel_draft(request):
    """Delete an existing draft for the user."""
    drafts = _get_drafts(request.user)
    if drafts:
        drafts.delete()
    else:
        msg = _("Unrecognized request or nothing to cancel.")
        content_type = None
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            msg = json.dumps({"status": "error", "message": msg})
            content_type = "application/json"
        return HttpResponseBadRequest(msg, content_type=content_type)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return HttpResponse(json.dumps({"status": "success"}), content_type="application/json")

    return HttpResponseRedirect(reverse("gallery.gallery"))


def gallery_async(request):
    """AJAX endpoint to media gallery.

    Returns an HTML list representation of the media.

    """
    term = request.GET.get("q")
    media_locale = request.GET.get("locale", settings.WIKI_DEFAULT_LANGUAGE)
    media_qs = Image.objects.filter(locale=media_locale)

    if term:
        media_qs = media_qs.filter(Q(title__icontains=term) | Q(description__icontains=term))

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    return render(request, "gallery/includes/media_list.html", {"media_list": media})


def search(request):
    """Search the media gallery."""

    term = request.GET.get("q")
    if not term:
        return HttpResponseRedirect(reverse("gallery.gallery"))

    filter = Q(title__icontains=term) | Q(description__icontains=term)
    media_qs = Image.objects.filter(filter, locale=request.LANGUAGE_CODE)

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    return render(request, "gallery/search.html", {"media": media, "q": term})


@login_required
def delete_media(request, media_id):
    """Delete media and redirect to gallery view."""
    media, media_format = _get_media_info(media_id)

    check_media_permissions(media, request.user, "delete")

    if request.method == "GET":
        # Render the confirmation page
        return render(
            request,
            "gallery/confirm_media_delete.html",
            {"media": media, "media_format": media_format},
        )

    # Handle confirm delete form POST
    log.warning("User {} is deleting image with id={}".format(request.user, media.id))
    media.delete()
    # Rebuild KB
    schedule_rebuild_kb()
    return HttpResponseRedirect(reverse("gallery.gallery"))


@login_required
def edit_media(request, media_id):
    """Edit media means only changing the description, for now."""
    media, media_format = _get_media_info(media_id)

    check_media_permissions(media, request.user, "change")

    media_form = _init_media_form(ImageForm, request, media, ("locale", "title"))

    if request.method == "POST" and media_form.is_valid():
        media = media_form.save(update_user=request.user, is_draft=None)
        return HttpResponseRedirect(reverse("gallery.media", args=[media_id]))

    return render(
        request,
        "gallery/edit_media.html",
        {
            "media": media,
            "media_format": media_format,
            "form": media_form,
        },
    )


def media(request, media_id):
    """The media page."""
    media, media_format = _get_media_info(media_id)
    return render(
        request,
        "gallery/media.html",
        {"media": media, "media_format": media_format},
    )


@login_required
@require_POST
@xframe_options_sameorigin
def upload_async(request):
    """Upload images from request.FILES."""
    # TODO(paul): validate the Submit File on upload modal async
    #             even better, use JS validation for title length.
    try:
        file_info = upload_image(request)
    except FileTooLargeError as e:
        return HttpResponseBadRequest(json.dumps({"status": "error", "message": e.args[0]}))

    if isinstance(file_info, dict) and "thumbnail_url" in file_info:
        schedule_rebuild_kb()
        return HttpResponse(json.dumps({"status": "success", "file": file_info}))

    message = _("Could not upload your image.")
    return HttpResponseBadRequest(
        json.dumps({"status": "error", "message": str(message), "errors": file_info})
    )


def _get_media_info(media_id):
    """Returns an image along with its media format."""
    media_format = None
    media = get_object_or_404(Image, pk=media_id)
    try:
        with PILImage.open(media.file.file) as img:
            media_format = img.format.lower() if img.format else None
    except UnidentifiedImageError, OSError:
        pass
    return (media, media_format)


def _get_drafts(user):
    """Get the image drafts for a given user."""
    if user.is_authenticated:
        return Image.objects.filter(creator=user, is_draft=True)
    return Image.objects.none()


def _init_media_form(form_cls, request=None, obj=None, ignore_fields=()):
    """Initializes the media form with an Image instance and POSTed data.

    form_cls is a django ModelForm
    Request method must be POST for POST data to be bound.
    exclude_fields contains the list of fields to default to their current
    value from the Image object.

    """
    post_data = None
    initial = None
    if request:
        initial = {"locale": request.LANGUAGE_CODE}
    file_data = None
    if request.method == "POST":
        file_data = request.FILES
        post_data = request.POST.copy()
        if obj and ignore_fields:
            for f in ignore_fields:
                post_data[f] = getattr(obj, f)

    return form_cls(post_data, file_data, instance=obj, initial=initial, is_ajax=False)
