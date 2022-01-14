from django.urls import re_path

from kitsune.products import api

# API urls
urlpatterns = [
    re_path(r"^$", api.ProductList.as_view(), name="product-list"),
    re_path(r"^(?P<product>[^/]+)/topic/?$", api.TopicList.as_view(), name="topic-list"),
    re_path(
        r"^(?P<product>[^/]+)/topic/(?P<topic>[^/]+)/?$",
        api.TopicDetail.as_view(),
        name="topic-detail",
    ),
]
