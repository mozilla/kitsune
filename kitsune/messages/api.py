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

    def get_suggestions(pre, is_staff=False):
        """Generate autocomplete suggestions for users and, if applicable, groups."""

        def create_suggestion(item, item_type, is_user=True):
            """Create a dictionary object for the autocomplete suggestion."""
            return {
                "type": item_type,
                "type_icon": webpack_static(
                    settings.DEFAULT_USER_ICON if is_user else settings.DEFAULT_GROUP_ICON
                ),
                "name": item.username if is_user else item.name,
                "display_name": item.profile.name if is_user else item.name,
                "avatar": profile_avatar(item, 24)
                if is_user
                else webpack_static(settings.DEFAULT_AVATAR),
            }

        def append_exact_match(pre, suggestions, is_staff):
            """Append the exact match to suggestions if not already included."""
            try:
                exact_match_user = (
                    User.objects.filter(username__iexact=pre, is_active=True)
                    .select_related("profile")
                    .get()
                )
                suggestions.append(create_suggestion(exact_match_user, "User"))
            except User.DoesNotExist:
                if is_staff:
                    try:
                        exact_match_group = Group.objects.get(name__iexact=pre)
                        suggestions.append(create_suggestion(exact_match_group, "Group", False))
                    except Group.DoesNotExist:
                        pass

        suggestions = []
        user_criteria = Q(username__istartswith=pre) | Q(profile__name__istartswith=pre)
        users = (
            User.objects.filter(user_criteria, is_active=True)
            .exclude(profile__is_fxa_migrated=False)
            .select_related("profile")[:10]
        )

        for user in users:
            suggestions.append(create_suggestion(user, "User"))

        if is_staff:
            groups = Group.objects.filter(name__istartswith=pre)[:10]
            for group in groups:
                suggestions.append(create_suggestion(group, "Group", False))

        append_exact_match(pre, suggestions, is_staff)
        return suggestions

    return get_suggestions(pre, request.user.profile.is_staff)
