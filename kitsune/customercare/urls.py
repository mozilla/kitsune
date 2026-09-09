from django.urls import re_path

from kitsune.customercare import views

urlpatterns = [
    re_path(
        r"^support-tickets/(?P<ticket_id>\d+)/update-topic$",
        views.update_topic,
        name="customercare.update_topic",
    ),
    re_path(
        r"^support-chat/jwt/(?P<product_slug>[^/]+)$",
        views.chat_jwt,
        name="customercare.chat_jwt",
    ),
]
