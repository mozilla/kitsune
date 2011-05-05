from django.conf.urls.defaults import patterns, url

from messages import views


urlpatterns = patterns('',
    url(r'^$', views.inbox, name='messages.inbox'),
    url(r'^/read/(?P<msgid>\d+)', views.read, name='messages.read'),
)
