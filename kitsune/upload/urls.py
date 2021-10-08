from django.urls import path

from kitsune.upload import views

urlpatterns = [
    path(
        "image/<str:model_name>/<int:object_pk>",
        views.up_image_async,
        name="upload.up_image_async",
    ),
    path("image/delete/<int:image_id>", views.del_image_async, name="upload.del_image_async"),
]
