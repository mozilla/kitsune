from django.urls import re_path

from kitsune.messages import views

urlpatterns = [
    re_path(r"^$", views.inbox, name="messages.inbox"),
    re_path(r"^bulk_action$", views.bulk_action, name="messages.bulk_action"),
    re_path(r"^read/(?P<msgid>\d+)$", views.read, name="messages.read"),
    re_path(r"^read/(?P<msgid>\d+)/delete$", views.delete, name="messages.delete"),
    re_path(r"^sent$", views.outbox, name="messages.outbox"),
    re_path(
        r"^sent/(?P<msgid>\d+)/delete$",
        views.delete,
        {"msgtype": "outbox"},
        name="messages.delete_outbox",
    ),
    re_path(
        r"^sent/bulk_action$",
        views.bulk_action,
        {"msgtype": "outbox"},
        name="messages.outbox_bulk_action",
    ),
    re_path(r"^sent/(?P<msgid>\d+)$", views.read_outbox, name="messages.read_outbox"),
    re_path(r"^new$", views.new_message, name="messages.new"),
    re_path(r"^preview-async$", views.preview_async, name="messages.preview_async"),
]
