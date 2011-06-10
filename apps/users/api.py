import json

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.http import require_GET

from statsd import statsd

from access.decorators import login_required


@login_required
@require_GET
def usernames(request):
    """An API to provide auto-complete data for user names."""
    mimetype = 'application/json'
    pre = request.GET.get('u', None)
    if not pre:
        return HttpResponse(json.dumps([]), mimetype=mimetype)

    # Eventually, when display name becomes more prominent, we'll want to
    # include that. Don't just OR this with Q(profile__name__startswith=pre).
    # That way lies horrid performance.
    with statsd.timer('users.api.usernames.search'):
        q = Q(username__istartswith=pre)
        users = User.objects.filter(q).values_list('username', flat=True)[0:5]
    # json.dumps won't serialize a QuerySet, so list comp.
    return HttpResponse(json.dumps([u for u in users]), mimetype=mimetype)
