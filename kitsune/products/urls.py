from django.conf.urls import patterns, url


urlpatterns = patterns('kitsune.products.views',
    url(r'^$', 'product_list', name='products'),
    url(r'^/(?P<slug>[^/]+)$', 'product_landing', name='products.product'),
    url(r'^/(?P<product_slug>[^/]+)/(?P<topic_slug>[^/]+)$',
        'document_listing', name='products.documents'),
    url(r'^/(?P<product_slug>[^/]+)/(?P<topic_slug>[^/]+)/(?P<subtopic_slug>[^/]+)$',
        'document_listing', name='products.subtopics'),
)
