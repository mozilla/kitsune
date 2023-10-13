import json

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from kitsune.access.decorators import login_required
from kitsune.upload.models import ImageAttachment
from kitsune.upload.utils import FileTooLargeError, upload_imageattachment

ALLOWED_MODELS = ["questions.Question", "questions.Answer", "auth.User"]


@login_required
@require_POST
@xframe_options_sameorigin
def up_image_async(request, model_name, object_pk):
    """Upload all images in request.FILES."""

    # Verify the model agaist our white-list
    if model_name not in ALLOWED_MODELS:
        message = _("Model not allowed.")
        return HttpResponseBadRequest(json.dumps({"status": "error", "message": message}))

    user = request.user
    # Get the model
    m = apps.get_model(*model_name.split("."))

    # Then look up the object by pk
    try:
        obj = m.objects.get(pk=object_pk)
    except ObjectDoesNotExist:
        message = _("Object does not exist.")
        return HttpResponseNotFound(json.dumps({"status": "error", "message": message}))

    # Reject the request if you're not a superuser, the owner of the object
    # or a member of the trusted contributors group
    if not any(
        [
            user.is_superuser,
            user == getattr(obj, "creator", obj),
            user.groups.filter(name="trusted contributors").exists(),
        ]
    ):
        message = _("You cannot associate an image with an object you do not own.")
        return HttpResponseBadRequest(json.dumps({"status": "error", "message": message}))

    try:
        file_info = upload_imageattachment(request, obj)
    except FileTooLargeError as e:
        return HttpResponseBadRequest(json.dumps({"status": "error", "message": e.args[0]}))

    if hasattr(obj, "clear_cached_images"):
        # if the object the image is attached to has a `clear_cached_images` method,
        # like questions and answers do, call it
        obj.clear_cached_images()

    if isinstance(file_info, dict) and "thumbnail_url" in file_info:
        return HttpResponse(json.dumps({"status": "success", "file": file_info}))

    message = _("Invalid or no image received.")
    return HttpResponseBadRequest(
        json.dumps({"status": "error", "message": message, "errors": file_info})
    )


@require_POST
@xframe_options_sameorigin
def del_image_async(request, image_id):
    """Delete an image given its object id."""
    user = request.user
    if not user.is_authenticated:
        message = _("You are not signed in.")
        return HttpResponseForbidden(json.dumps({"status": "error", "message": message}))

    try:
        image = ImageAttachment.objects.get(pk=image_id)
    except ImageAttachment.DoesNotExist:
        message = _("The requested image could not be found.")
        return HttpResponseNotFound(json.dumps({"status": "error", "message": message}))

    if not ((user == image.creator) or (user.has_perm("upload.delete_imageattachment"))):
        message = _("You do not have permission to do that.")
        return HttpResponseForbidden(json.dumps({"status": "error", "message": message}))

    content_object = image.content_object

    image.file.delete()
    if image.thumbnail:
        image.thumbnail.delete()
    image.delete()

    if hasattr(content_object, "clear_cached_images"):
        # if the object the image was attached to has a `clear_cached_images` method,
        # like questions and answers do, call it
        content_object.clear_cached_images()

    return HttpResponse(json.dumps({"status": "success"}))
