from django.conf.urls import url

from kitsune.products import api


# API urls
urlpatterns = [
    url(r"^$", api.ProductList.as_view(), name="product-list"),
    url(r"^(?P<product>[^/]+)/topic/?$", api.TopicList.as_view(), name="topic-list"),
    url(
        r"^(?P<product>[^/]+)/topic/(?P<topic>[^/]+)/?$",
        api.TopicDetail.as_view(),
        name="topic-detail",
    ),
]
