from django.views.decorators.http import require_GET

from kitsune.access.decorators import login_required
from kitsune.messages.utils import create_suggestion, find_users_and_groups_by_search
from kitsune.sumo.decorators import json_view


@login_required
@require_GET
@json_view
def get_autocomplete_suggestions(request):
    """An API to provide auto-complete data for user names or groups."""
    pre = request.GET.get("term", "") or request.GET.get("query", "")
    if not pre or not request.user.is_authenticated:
        return []
    users_and_groups = find_users_and_groups_by_search(
        pre, show_groups=request.user.profile.in_staff_group
    )
    suggestions = [create_suggestion(obj) for obj in users_and_groups]
    return suggestions
