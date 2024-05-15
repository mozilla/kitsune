from django.urls import include, re_path

from kitsune.products import views

product_patterns = [
    re_path(r"^$", views.product_list, name="products"),
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

topic_patterns = [
    re_path(r"^(?P<topic_slug>[^/]+)$", views.document_listing, name="products.topic_documents"),
    re_path(
        r"(?P<topic_slug>[^/]+)/(?P<product_slug>[^/]+)$",
        views.document_listing,
        name="products.topic_product_documents",
    ),
]

urlpatterns = [
    re_path(r"^products/", include(product_patterns)),
    re_path(r"^topics/", include(topic_patterns)),
]
