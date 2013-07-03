from django.conf.urls import patterns, url

# Note tha these url do not get considered into the locale middleware.
# http://<base>/offline/get-bundles ... etc.
urlpatterns = patterns('kitsune.offline.views',
    url(r'^/get-bundle$', 'get_bundle', name='offline.get_bundle'),
    url(r'^/bundle-version', 'bundle_version', name='offline.bundle_version')
)
