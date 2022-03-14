from django.urls import re_path

from kitsune.wiki import api

# API urls
urlpatterns = [
    re_path(r"^$", api.DocumentList.as_view(), name="document-list"),
    re_path(r"^(?P<slug>[^/]+)$", api.DocumentDetail.as_view(), name="document-detail"),
]
