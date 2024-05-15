from django.urls import re_path

from kitsune.products import views

urlpatterns = [
    re_path(r"^products/", views.product_list, name="products"),
    re_path(r"^topics$", views.topic_list, name="products.topics"),
    re_path(r"^topics/(?P<product_slug>[^/]+)$", views.topic_list, name="products.topics"),
    re_path(r"^(?P<slug>[^/]+)$", views.product_landing, name="products.product"),
    re_path(
        r"^(?P<product_slug>[^/]+)/(?P<topic_slug>[^/]+)$",
        views.document_listing,
        name="products.documents",
    ),
    re_path(
        r"^(?P<product_slug>[^/]+)/(?P<topic_slug>[^/]+)/" r"(?P<subtopic_slug>[^/]+)$",
        views.document_listing,
        name="products.subtopics",
    ),
]
