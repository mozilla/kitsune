from django_jinja import library

from kitsune.announcements.models import Announcement
from kitsune.announcements.utils import detect_platform_from_user_agent


@library.global_function
def get_announcements(request):
    user = request.user if request.user.is_authenticated else None

    user_platforms = detect_platform_from_user_agent(request)

    if user:
        user_groups = user.groups.values_list("id", flat=True)
        return Announcement.get_for_groups(user_groups, platform_slugs=user_platforms)

    return Announcement.get_site_wide(platform_slugs=user_platforms)
