from django.conf.urls import url

from kitsune.products import views


urlpatterns = [
    url(r'^$', views.product_list, name='products'),
    url(r'^/(?P<slug>[^/]+)$', views.product_landing, name='products.product'),
    url(r'^/(?P<product_slug>[^/]+)/(?P<topic_slug>[^/]+)$',
        views.document_listing, name='products.documents'),
    url(r'^/(?P<product_slug>[^/]+)/(?P<topic_slug>[^/]+)/'
        r'(?P<subtopic_slug>[^/]+)$',
        views.document_listing, name='products.subtopics'),
]
