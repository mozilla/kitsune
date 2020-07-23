from django.conf.urls import url

from kitsune.gallery import api


# API urls
urlpatterns = [
    url(r"^image/?$", api.ImageList.as_view(), name="image-list"),
    url(r"^image/(?P<pk>\d+)/?$", api.ImageDetail.as_view(), name="image-detail"),
]
