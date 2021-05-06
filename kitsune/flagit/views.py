import json
from kitsune.questions.events import QuestionReplyEvent
from kitsune.questions.models import Answer

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from kitsune.access.decorators import permission_required, login_required
from kitsune.flagit.models import FlaggedObject
from kitsune.sumo.urlresolvers import reverse


@require_POST
@login_required
def flag(request, content_type=None, model=None, object_id=None, **kwargs):
    if not content_type:
        if model:
            content_type = ContentType.objects.get_for_model(model).id
        else:
            content_type = request.POST.get("content_type")

    if not object_id:
        object_id = int(request.POST.get("object_id"))

    reason = request.POST.get("reason")
    notes = request.POST.get("other", "")
    next = request.POST.get("next")

    content_type = get_object_or_404(ContentType, id=int(content_type))
    object_id = int(object_id)
    content_object = get_object_or_404(content_type.model_class(), pk=object_id)

    # Check that this user hasn't already flagged the object
    try:
        FlaggedObject.objects.get(
            content_type=content_type, object_id=object_id, creator=request.user
        )
        msg = _("You already flagged this content.")
    except FlaggedObject.DoesNotExist:
        flag = FlaggedObject(
            content_object=content_object, reason=reason, creator=request.user, notes=notes
        )
        flag.save()
        msg = _("You have flagged this content. A moderator will review your submission shortly.")

    if request.is_ajax():
        return HttpResponse(json.dumps({"message": msg}))
    elif next:
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(next)

    return HttpResponse(msg)


@login_required
@permission_required("flagit.can_moderate")
def queue(request, content_type=None):
    """The moderation queue."""
    return render(request, "flagit/queue.html", {"objects": FlaggedObject.objects.pending()})


@require_POST
@login_required
@permission_required("flagit.can_moderate")
def update(request, flagged_object_id):
    """Update the status of a flagged object."""
    flagged = get_object_or_404(FlaggedObject, pk=flagged_object_id)
    new_status = request.POST.get("status")
    if new_status:
        ct = flagged.content_type
        # If the object is an Answer let's fire a notification
        # if the flag is invalid
        if str(new_status) == str(FlaggedObject.FLAG_REJECTED) and ct.model_class() == Answer:
            answer = flagged.content_object
            QuestionReplyEvent(answer).fire(exclude=answer.creator)

        flagged.status = new_status
        flagged.save()

    return HttpResponseRedirect(reverse("flagit.queue"))
