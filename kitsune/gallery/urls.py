from django.conf.urls import url

from kitsune.gallery import views
from kitsune.sumo.views import redirect_to


urlpatterns = [
    url(
        r"^$", redirect_to, {"url": "gallery.gallery", "media_type": "image"}, name="gallery.home"
    ),
    url(r"^/async$", views.gallery_async, name="gallery.async"),
    url(r"^/(?P<media_type>\w+)s$", views.gallery, name="gallery.gallery"),
    url(r"^/(?P<media_type>\w+)s/search$", views.search, name="gallery.search"),
    url(r"^/(?P<media_type>\w+)s/upload$", views.upload, name="gallery.upload"),
    url(r"^/(?P<media_type>\w+)s/cancel_draft$", views.cancel_draft, name="gallery.cancel_draft"),
    url(r"^/(?P<media_type>\w+)/upload_async$", views.upload_async, name="gallery.upload_async"),
    url(
        r"^/(?P<media_type>\w+)/(?P<media_id>\d+)/delete$",
        views.delete_media,
        name="gallery.delete_media",
    ),
    url(
        r"^/(?P<media_type>\w+)/(?P<media_id>\d+)/edit$",
        views.edit_media,
        name="gallery.edit_media",
    ),
    url(r"^/(?P<media_type>\w+)/(?P<media_id>\d+)$", views.media, name="gallery.media"),
]
