from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('notifications.views',
    url(r'^unsubscribe/(?P<watch_id>\d+)$',
        'unsubscribe',
        name='notifications.unsubscribe')
)
