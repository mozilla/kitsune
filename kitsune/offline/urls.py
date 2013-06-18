from django.conf.urls import patterns, url

# Note tha these url do not get considered into the locale middleware.
# http://<base>/offline/get-bundles ... etc.
urlpatterns = patterns('kitsune.offline.views',
    url(r'^/get-bundles$', 'get_bundles', name='offline.get_bundles'),
    url(r'^/get-languages$', 'get_languages', name='offline.get_languages')
)
