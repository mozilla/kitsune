from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.views.decorators.http import require_GET

from kitsune.access.decorators import login_required
from kitsune.sumo.decorators import json_view
from kitsune.sumo.utils import webpack_static
from kitsune.users.templatetags.jinja_helpers import profile_avatar


@login_required
@require_GET
@json_view
def get_autocomplete_suggestions(request):
    """An API to provide auto-complete data for user names or groups."""
    pre = request.GET.get("term", "") or request.GET.get("query", "")
    if not pre or not request.user.is_authenticated:
        return []

    def create_suggestion(item):
        """Create a dictionary object for the autocomplete suggestion."""
        is_user = isinstance(item, User)
        return {
            "type": "User" if is_user else "Group",
            "type_icon": webpack_static(
                settings.DEFAULT_USER_ICON if is_user else settings.DEFAULT_GROUP_ICON
            ),
            "name": item.username if is_user else item.name,
            "type_and_name": f"User: {item.username}" if is_user else f"Group: {item.name}",
            "display_name": item.profile.name if is_user else item.name,
            "avatar": (
                profile_avatar(item, 24) if is_user else webpack_static(settings.DEFAULT_AVATAR)
            ),
        }

    suggestions = []
    user_criteria = Q(username__istartswith=pre) | Q(profile__name__istartswith=pre)
    users = User.objects.filter(user_criteria, is_active=True).select_related("profile")[:10]

    for user in users:
        suggestions.append(create_suggestion(user))

    if request.user.profile.in_staff_group:
        groups = Group.objects.filter(name__istartswith=pre, profile__isnull=False)[:10]
        for group in groups:
            suggestions.append(create_suggestion(group))

    return suggestions
