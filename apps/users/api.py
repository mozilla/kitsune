from django.contrib.auth.models import User
from django.db.models import Q
from django.views.decorators.http import require_GET

from statsd import statsd

from sumo.decorators import json_view
from access.decorators import login_required


@login_required
@require_GET
@json_view
def usernames(request):
    """An API to provide auto-complete data for user names."""
    pre = request.GET.get('term', '')

    if not pre:
        return []
    if not request.user.is_authenticated():
        return []
    # Eventually, when display name becomes more prominent, we'll want to
    # include that. Don't just OR this with Q(profile__name__startswith=pre).
    # That way lies horrid performance.
    with statsd.timer('users.api.usernames.search'):
        users = User.objects.exclude(
            ~Q(username__istartswith=pre),
            ~Q(email__istartswith=pre)
            ).values('username', 'email')[:10]
        return list(users)
