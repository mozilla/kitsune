from django.conf.urls import url

from kitsune.upload import views


urlpatterns = [
    url(
        r"^/image/(?P<model_name>\w+\.\w+)/(?P<object_pk>\d+)$",
        views.up_image_async,
        name="upload.up_image_async",
    ),
    url(
        r"^/image/delete/(?P<image_id>\d+)$", views.del_image_async, name="upload.del_image_async"
    ),
]
