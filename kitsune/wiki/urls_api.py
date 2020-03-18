from django.conf.urls import url

from kitsune.wiki import api


# API urls
urlpatterns = [
    url(r"^$", api.DocumentList.as_view(), name="document-list"),
    url(r"^(?P<slug>[^/]+)$", api.DocumentDetail.as_view(), name="document-detail"),
]
