import json

from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import get_model
from django.http import (HttpResponse, HttpResponseNotFound,
                         HttpResponseBadRequest, HttpResponseForbidden)
from django.views.decorators.clickjacking import xframe_options_sameorigin

from tower import ugettext as _

from access.decorators import login_required
from upload.models import ImageAttachment
from upload.utils import upload_imageattachment, FileTooLargeError


ALLOWED_MODELS = ['questions.Question', 'questions.Answer']


@login_required
@require_POST
@xframe_options_sameorigin
def up_image_async(request, model_name, object_pk):
    """Upload all images in request.FILES."""

    # Verify the model agaist our white-list
    if model_name not in ALLOWED_MODELS:
        message = _('Model not allowed.')
        return HttpResponseBadRequest(
            json.dumps({'status': 'error', 'message': message}))

    # Get the model
    m = get_model(*model_name.split('.'))

    # Then look up the object by pk
    try:
        obj = m.objects.get(pk=object_pk)
    except ObjectDoesNotExist:
        message = _('Object does not exist.')
        return HttpResponseNotFound(
            json.dumps({'status': 'error', 'message': message}))

    try:
        file_info = upload_imageattachment(request, obj)
    except FileTooLargeError as e:
        return HttpResponseBadRequest(
            json.dumps({'status': 'error', 'message': e.args[0]}))

    if isinstance(file_info, dict) and 'thumbnail_url' in file_info:
        return HttpResponse(
            json.dumps({'status': 'success', 'file': file_info}))

    message = _('Invalid or no image received.')
    return HttpResponseBadRequest(
        json.dumps({'status': 'error', 'message': message,
                    'errors': file_info}))


@require_POST
@xframe_options_sameorigin
def del_image_async(request, image_id):
    """Delete an image given its object id."""
    user = request.user
    if not user.is_authenticated():
        message = _('You are not logged in.')
        return HttpResponseForbidden(
            json.dumps({'status': 'error', 'message': message}))

    try:
        image = ImageAttachment.objects.get(pk=image_id)
    except ImageAttachment.DoesNotExist:
        message = _('The requested image could not be found.')
        return HttpResponseNotFound(
            json.dumps({'status': 'error', 'message': message}))

    if not ((user == image.creator) or
            (user.has_perm('upload.delete_imageattachment'))):
        message = _('You do not have permission to do that.')
        return HttpResponseForbidden(
            json.dumps({'status': 'error', 'message': message}))

    image.file.delete()
    if image.thumbnail:
        image.thumbnail.delete()
    image.delete()

    return HttpResponse(json.dumps({'status': 'success'}))
