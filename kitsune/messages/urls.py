from django.conf.urls import patterns, url

from kitsune.messages import views


urlpatterns = patterns(
    '',
    url(r'^$', views.inbox, name='messages.inbox'),
    url(r'^/bulk_action$', views.bulk_action, name='messages.bulk_action'),
    url(r'^/read/(?P<msgid>\d+)$', views.read, name='messages.read'),
    url(r'^/read/(?P<msgid>\d+)/delete$', views.delete,
        name='messages.delete'),
    url(r'^/sent$', views.outbox, name='messages.outbox'),
    url(r'^/sent/(?P<msgid>\d+)/delete$', views.delete,
        {'msgtype': 'outbox'}, name='messages.delete_outbox'),
    url(r'^/sent/bulk_action$', views.bulk_action,
        {'msgtype': 'outbox'}, name='messages.outbox_bulk_action'),
    url(r'^/sent/(?P<msgid>\d+)$', views.read_outbox,
        name='messages.read_outbox'),
    url(r'^/new$', views.new_message, name='messages.new'),
    url(r'^/preview-async$', views.preview_async,
        name='messages.preview_async'),
)
