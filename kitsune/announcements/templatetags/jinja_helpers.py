from django_jinja import library

from kitsune.announcements.models import Announcement


@library.global_function
def get_announcements():
    return Announcement.get_site_wide()
