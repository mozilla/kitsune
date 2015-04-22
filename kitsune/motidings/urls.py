from django.conf.urls import patterns, url


# Note: This overrides the tidings tidings.unsubscribe url pattern, so
# we need to keep the name exactly as it is.
urlpatterns = patterns(
    'kitsune.motidings.views',
    url(r'^unsubscribe/(?P<watch_id>\d+)$',
        'unsubscribe',
        name='tidings.unsubscribe')
)
