from django.conf import settings
from django.conf.urls.defaults import patterns, url, include

from sumo import views


services_patterns = patterns('',
    url('^/monitor$', views.monitor, name='sumo.monitor'),
)


urlpatterns = patterns('',
    url(r'^robots.txt$', views.robots, name='robots.txt'),
    ('^services', include(services_patterns)),
)


if 'django_qunit' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^qunit/(?P<path>.*)', views.kitsune_qunit),
        url(r'^_qunit/', include('django_qunit.urls')),
    )
