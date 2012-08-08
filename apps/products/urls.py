from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('products.views',
    url(r'^$', 'product_list', name='products'),
    url(r'^/(?P<slug>[^/]+)$', 'product_landing', name='products.product'),
)
