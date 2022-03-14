from django.urls import re_path

from kitsune.gallery import views
from kitsune.sumo.views import redirect_to

urlpatterns = [
    re_path(
        r"^$", redirect_to, {"url": "gallery.gallery", "media_type": "image"}, name="gallery.home"
    ),
    re_path(r"^/async$", views.gallery_async, name="gallery.async"),
    re_path(r"^/(?P<media_type>\w+)s$", views.gallery, name="gallery.gallery"),
    re_path(r"^/(?P<media_type>\w+)s/search$", views.search, name="gallery.search"),
    re_path(r"^/(?P<media_type>\w+)s/upload$", views.upload, name="gallery.upload"),
    re_path(
        r"^/(?P<media_type>\w+)s/cancel_draft$", views.cancel_draft, name="gallery.cancel_draft"
    ),
    re_path(
        r"^/(?P<media_type>\w+)/upload_async$", views.upload_async, name="gallery.upload_async"
    ),
    re_path(
        r"^/(?P<media_type>\w+)/(?P<media_id>\d+)/delete$",
        views.delete_media,
        name="gallery.delete_media",
    ),
    re_path(
        r"^/(?P<media_type>\w+)/(?P<media_id>\d+)/edit$",
        views.edit_media,
        name="gallery.edit_media",
    ),
    re_path(r"^/(?P<media_type>\w+)/(?P<media_id>\d+)$", views.media, name="gallery.media"),
]
