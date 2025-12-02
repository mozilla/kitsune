from django.urls import re_path

from kitsune.flagit import views

urlpatterns = [
    re_path(r"^flagged$", views.flagged_queue, name="flagit.flagged_queue"),
    re_path(r"^moderate$", views.moderate_content, name="flagit.moderate_content"),
    re_path(r"^zendesk-spam$", views.zendesk_spam_queue, name="flagit.zendesk_spam_queue"),
    re_path(r"^flag$", views.flag, name="flagit.flag"),
    re_path(r"^update/(?P<flagged_object_id>\d+)$", views.update, name="flagit.update"),
]
