import json
import logging
import posixpath

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST, require_safe
from PIL import Image as PILImage
from PIL import UnidentifiedImageError

from kitsune.access.decorators import login_required
from kitsune.gallery import ITEMS_PER_PAGE
from kitsune.gallery.forms import PUBLIC_KNOWLEDGE_BASE, ImageForm, KnowledgeBaseForm
from kitsune.gallery.models import Image
from kitsune.gallery.storage import private_images_enabled, private_storage
from kitsune.gallery.utils import (
    can_upload_to,
    check_media_permissions,
    upload_image,
    upload_knowledge_bases,
)
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import mark_private, paginate, smart_int
from kitsune.sumo.views import handle404
from kitsune.upload.tasks import compress_image, generate_thumbnail
from kitsune.upload.utils import FileTooLargeError
from kitsune.wiki.models import Audience
from kitsune.wiki.tasks import schedule_rebuild_kb

log = logging.getLogger("k.gallery")

PRIVATE_MEDIA_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
}
# A revoked member's browser may keep showing an already-seen image for this long.
PRIVATE_MEDIA_MAX_AGE = 600


def render_gallery(request, template_name, context, *, private):
    """Renders the page; private content stays out of shared caches, referrers and analytics."""
    if private:
        context["suppress_analytics"] = True
    response = render(request, template_name, context)
    return mark_private(response) if private else response


def gallery(request):
    """The media gallery."""
    media_qs = Image.objects.public().filter(locale=request.LANGUAGE_CODE)
    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    drafts = _get_drafts(request.user)
    image = drafts[0] if drafts else None
    image_form = _init_media_form(ImageForm, request, image)
    if request.method == "POST":
        image_form.is_valid()

    knowledge_base_form = None
    knowledge_bases = upload_knowledge_bases(request.user)
    if knowledge_bases is not None:
        knowledge_base_form = KnowledgeBaseForm(
            knowledge_bases=knowledge_bases, draft=image, preselect=request.GET.get("kb")
        )

    return render_gallery(
        request,
        "gallery/gallery.html",
        {
            "media": media,
            "image_form": image_form,
            "knowledge_base_form": knowledge_base_form,
            "submitted": request.method == "POST",
            "locale": request.LANGUAGE_CODE,
        },
        # The upload form names private knowledge bases.
        private=knowledge_base_form is not None,
    )


@login_required
@require_POST
def upload(request):
    """Finalizes an uploaded draft."""
    drafts = _get_drafts(request.user)
    if drafts:
        # We're publishing an image draft!
        # Before validating: the title check reads the knowledge base's titles.
        if not can_upload_to(request.user, drafts[0].audience):
            raise PermissionDenied
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

    Returns an HTML list representation of the media: the public images, or those of the
    private knowledge base "kb" when it is one the user may pick from.

    """
    term = request.GET.get("q")
    media_locale = request.GET.get("locale", settings.WIKI_DEFAULT_LANGUAGE)
    kb = smart_int(request.GET.get("kb"))
    knowledge_base = None
    if kb > 0 and private_images_enabled():
        knowledge_base = Audience.objects.private_for(request.user).filter(pk=kb).first()

    if knowledge_base:
        media_qs = Image.objects.private_in(knowledge_base)
    else:
        media_qs = Image.objects.public()
    media_qs = media_qs.filter(locale=media_locale)

    if term:
        media_qs = media_qs.filter(Q(title__icontains=term) | Q(description__icontains=term))

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    return render_gallery(
        request,
        "gallery/includes/media_list.html",
        {"media_list": media},
        private=knowledge_base is not None,
    )


def search(request):
    """Search the media gallery."""

    term = request.GET.get("q")
    if not term:
        return HttpResponseRedirect(reverse("gallery.gallery"))

    filter = Q(title__icontains=term) | Q(description__icontains=term)
    media_qs = Image.objects.public().filter(filter, locale=request.LANGUAGE_CODE)

    media = paginate(request, media_qs, per_page=ITEMS_PER_PAGE)

    return render(request, "gallery/search.html", {"media": media, "q": term})


@login_required
def delete_media(request, media_id):
    """Delete media and redirect to gallery view."""
    media, media_format = _get_media_info(media_id, request.user)

    check_media_permissions(media, request.user, "delete")

    if request.method == "GET":
        # Render the confirmation page
        return render_gallery(
            request,
            "gallery/confirm_media_delete.html",
            {"media": media, "media_format": media_format},
            private=media.is_private,
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
    media, media_format = _get_media_info(media_id, request.user)

    check_media_permissions(media, request.user, "change")
    if (
        request.method == "POST"
        and media.is_draft
        and not can_upload_to(request.user, media.audience)
    ):
        raise PermissionDenied

    media_form = _init_media_form(ImageForm, request, media, ("locale", "title"))

    if request.method == "POST" and media_form.is_valid():
        media = media_form.save(update_user=request.user, is_draft=None)
        return HttpResponseRedirect(reverse("gallery.media", args=[media_id]))

    return render_gallery(
        request,
        "gallery/edit_media.html",
        {
            "media": media,
            "media_format": media_format,
            "form": media_form,
        },
        private=media.is_private,
    )


def media(request, media_id):
    """The media page."""
    media, media_format = _get_media_info(media_id, request.user)
    return render_gallery(
        request,
        "gallery/media.html",
        {"media": media, "media_format": media_format},
        private=media.is_private,
    )


@login_required
@require_POST
@xframe_options_sameorigin
def upload_async(request):
    """
    Upload images from request.FILES, into the knowledge base the uploader chose. Users who
    can't upload private images make no choice: their images are public.
    """
    # TODO(paul): validate the Submit File on upload modal async
    #             even better, use JS validation for title length.
    knowledge_bases = upload_knowledge_bases(request.user)
    if knowledge_bases is None:
        choice = request.POST.get("knowledge_base", "")
        audience = Audience.objects.default() if choice in ("", PUBLIC_KNOWLEDGE_BASE) else None
    else:
        form = KnowledgeBaseForm(request.POST, knowledge_bases=knowledge_bases)
        audience = form.cleaned_data["knowledge_base"] if form.is_valid() else None

    if audience is None:
        message = _("Please choose who can see the image.")
        return HttpResponseBadRequest(json.dumps({"status": "error", "message": str(message)}))

    try:
        file_info = upload_image(request, audience)
    except FileTooLargeError as e:
        return HttpResponseBadRequest(json.dumps({"status": "error", "message": e.args[0]}))

    if isinstance(file_info, dict) and "thumbnail_url" in file_info:
        schedule_rebuild_kb()
        return HttpResponse(json.dumps({"status": "success", "file": file_info}))

    message = _("Could not upload your image.")
    return HttpResponseBadRequest(
        json.dumps({"status": "error", "message": str(message), "errors": file_info})
    )


def private_media_404(request):
    # CacheHeadersMiddleware skips error responses, so a CDN would otherwise cache this 404.
    return mark_private(handle404(request))


@require_safe
def private_media(request, name):
    """
    Streams the file or thumbnail of a private image to those who may read the image. Every
    failure is the same 404, so nothing tells a missing image from one the viewer can't read.
    """
    # PostgreSQL rejects a NUL in a lookup value, which would be a 500 instead of the 404.
    if "\0" in name:
        return private_media_404(request)

    content_type = PRIVATE_MEDIA_CONTENT_TYPES.get(posixpath.splitext(name)[1].lower())
    storage = private_storage()
    if content_type is None or storage is None:
        return private_media_404(request)

    try:
        image = Image.objects.select_related("audience").get(Q(file=name) | Q(thumbnail=name))
    except Image.DoesNotExist, Image.MultipleObjectsReturned:
        return private_media_404(request)

    if not image.is_readable_by(request.user):
        return private_media_404(request)

    try:
        file = storage.open(name)
    except FileNotFoundError:
        return private_media_404(request)

    return FileResponse(
        file,
        filename=posixpath.basename(name),
        content_type=content_type,
        headers={
            "Cache-Control": f"private, max-age={PRIVATE_MEDIA_MAX_AGE}",
            "Vary": "Cookie, Authorization",
            "X-Content-Type-Options": "nosniff",
            "Cross-Origin-Resource-Policy": "same-origin",
        },
    )


def _get_media_info(media_id, user):
    """The image and its format; a private image the user can't read is a 404."""
    media_format = None
    media = get_object_or_404(Image.objects.select_related("audience"), pk=media_id)
    if not media.is_readable_by(user):
        raise Http404

    try:
        with PILImage.open(media.file.file) as img:
            media_format = img.format.lower() if img.format else None
    except UnidentifiedImageError, OSError:
        pass
    return (media, media_format)


def _get_drafts(user):
    """Get the image drafts for a given user."""
    if user.is_authenticated:
        return Image.objects.filter(creator=user, is_draft=True).select_related("audience")
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
        # The stored file stays; a replacement would follow the KB's current visibility.
        file_data = None if obj else request.FILES
        post_data = request.POST.copy()
        if obj and ignore_fields:
            for f in ignore_fields:
                post_data[f] = getattr(obj, f)

    return form_cls(post_data, file_data, instance=obj, initial=initial, is_ajax=False)
