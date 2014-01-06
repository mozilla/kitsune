from django.conf.urls import patterns, url

# Note that these url do not get considered into the locale middleware.
# http://<base>/offline/get-bundle ... etc.
urlpatterns = patterns(
    'kitsune.offline.views',
    url(r'^/get-bundle$', 'get_bundle', name='offline.get_bundle'),
    url(r'^/bundle-meta$', 'bundle_meta', name='offline.bundle_meta'),
    url(r'^/get-languages$', 'get_languages', name='offline.get_languages')
)
