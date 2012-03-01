from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.views.decorators.http import require_GET
from users.models import Profile

from statsd import statsd

from sumo.decorators import json_view
from access.decorators import login_required


def display_name_or_none(user):
    try:
        return user.profile.name
    except (Profile.DoesNotExist, AttributeError):
        return None


@login_required
@require_GET
@json_view
def usernames(request):
    """An API to provide auto-complete data for user names."""
    term = request.GET.get('term', '')
    query = request.GET.get('query', '')
    pre = term or query

    last_login = datetime.now() - timedelta(weeks=12)

    if not pre:
        return []
    if not request.user.is_authenticated():
        return []
    with statsd.timer('users.api.usernames.search'):
        profiles = Profile.objects.filter(
            Q(name__istartswith=pre)
            ).values_list('user_id', flat=True)
        users = User.objects.filter(
            Q(username__istartswith=pre) | Q(id__in=profiles),
            ).filter(last_login__gte=last_login
            ).extra(select={'length':'Length(username)'}
            ).order_by('length'
            ).select_related('profile')[:10]
        return [{'username':u.username,
                'display_name':display_name_or_none(u)}
                for u in users]
