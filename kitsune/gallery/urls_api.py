from django.urls import re_path

from kitsune.gallery import api

# API urls
urlpatterns = [
    re_path(r"^image/?$", api.ImageList.as_view(), name="image-list"),
    re_path(r"^image/(?P<pk>\d+)/?$", api.ImageDetail.as_view(), name="image-detail"),
]
