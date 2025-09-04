from django_jinja import library

from kitsune.announcements.models import Announcement
from kitsune.announcements.utils import detect_platform_from_user_agent


@library.global_function
def get_announcements(request):
    user = request.user if request.user.is_authenticated else None

    user_platforms = detect_platform_from_user_agent(request)
    user_groups = user.groups.values_list("id", flat=True) if user else None

    return Announcement.get_site_wide(
        platform_slugs=user_platforms, group_ids=user_groups, locale_name=request.LANGUAGE_CODE
    )
