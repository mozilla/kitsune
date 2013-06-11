from jingo import register

from kitsune.announcements.models import Announcement


@register.function
def get_announcements():
    return Announcement.get_site_wide()
