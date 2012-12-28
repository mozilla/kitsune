from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('announcements.views',
    url(r'^/create/locale$', 'create_for_locale',
        name='announcements.create_for_locale'),
    url(r'^/(?P<announcement_id>\d+)/delete$', 'delete',
        name='announcements.delete'),
)
