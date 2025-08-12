import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from kitsune.access.decorators import login_required
from kitsune.announcements.forms import AnnouncementForm
from kitsune.announcements.models import Announcement
from kitsune.announcements.templatetags.jinja_helpers import get_announcements
from kitsune.wiki.models import Locale


@require_POST
@login_required
def create_for_locale(request):
    """An ajax view to create a new announcement for the current locale."""
    user = request.user
    locale = Locale.objects.get(locale=request.LANGUAGE_CODE)

    if not user_can_announce(user, locale):
        return HttpResponseForbidden()

    form = AnnouncementForm(request.POST)

    if form.is_valid():
        platforms = form.cleaned_data.pop('platforms', [])
        a = Announcement(creator=user, locale=locale, **form.cleaned_data)
        a.save()

        if platforms:
            a.platforms.set(platforms)

        return HttpResponse(json.dumps({"id": a.id}), content_type="application/json")
    return HttpResponse(json.dumps(form.errors), status=400, content_type="application/json")


@require_POST
@login_required
def delete(request, announcement_id):
    """An ajax view to delete an announcement."""
    user = request.user
    locale = Locale.objects.get(locale=request.LANGUAGE_CODE)

    if not user_can_announce(user, locale):
        return HttpResponseForbidden()

    a = get_object_or_404(Announcement, id=announcement_id)
    a.delete()

    return HttpResponse("", status=204)


def announcements_for_platform(request):
    """Return announcements for a specific platform (JavaScript-first approach)."""
    platform = request.GET.get('platform', 'web')
    if platform not in ['win10', 'win11', 'mac', 'linux', 'android', 'web']:
        platform = 'web'

    if not hasattr(request, 'user'):
        request.user = AnonymousUser()

    original_platform = request.META.get('_JS_PLATFORM')
    request.META['_JS_PLATFORM'] = platform

    try:
        announcements = get_announcements(request)
        # Render using the same fragment template as base.html
        html = render_to_string('announcements/fragments/js_first_announcements.html', {
            'announcements': announcements,
            'request': request,
            'settings': settings
        })
        return HttpResponse(html)
    finally:
        if original_platform is not None:
            request.META['_JS_PLATFORM'] = original_platform
        else:
            request.META.pop('_JS_PLATFORM', None)


def user_can_announce(user, locale):
    if user.is_anonymous:
        return False
    return user.has_perm("announcements.add_announcement") or user in locale.leaders.all()
