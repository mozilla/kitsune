import json

from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from access.decorators import login_required

from announcements.forms import AnnouncementForm
from announcements.models import Announcement
from wiki.models import Locale


@require_POST
@login_required
def create_for_locale(request):
    """An ajax view to create a new announcement for the current locale."""
    user = request.user
    locale = Locale.objects.get(locale=request.locale)

    if not user_can_announce(user, locale):
        return HttpResponseForbidden()

    form = AnnouncementForm(request.POST)

    if form.is_valid():
        a = Announcement(creator=user, locale=locale, **form.cleaned_data)
        a.save()
        return HttpResponse(json.dumps({'id': a.id}))
    else:
        return HttpResponse(json.dumps(form.errors), status=400,
            content_type="application/json")


@require_POST
@login_required
def delete(request, announcement_id):
    """An ajax view to delete an announcement."""
    user = request.user
    locale = Locale.objects.get(locale=request.locale)

    if not user_can_announce(user, locale):
        return HttpResponseForbidden()

    a = get_object_or_404(Announcement, id=announcement_id)
    a.delete()

    return HttpResponse("", status=204)


def user_can_announce(user, locale):
    if user.is_anonymous():
        return False
    return user.has_perm('announce.create') or user in locale.leaders.all()
