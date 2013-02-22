from django.conf.urls import patterns, url

urlpatterns = patterns('chat.views',
    url(r'^$', 'chat', name='chat.home'),
    url(r'^/queue-status$', 'queue_status', name='chat.queue-status'),
)
