from django.urls import re_path

from kitsune.customercare import views

urlpatterns = [
    re_path(
        r"^support-tickets/(?P<ticket_id>\d+)/update-topic$",
        views.update_topic,
        name="customercare.update_topic",
    ),
    re_path(
        r"^support-tickets/(?P<ticket_id>\d+)/replies/(?P<outbox_id>\d+)/retry$",
        views.retry_outbox_reply,
        name="customercare.retry_outbox_reply",
    ),
]
