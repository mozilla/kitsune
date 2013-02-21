from django.conf import settings
from django.conf.urls.defaults import patterns, url, include
from django.views.generic.base import RedirectView

from sumo import views


services_patterns = patterns('',
    url('^/monitor$', views.monitor, name='sumo.monitor'),
    url('^/version$', views.version_check, name='sumo.version'),
    url('^/error$', views.error, name='sumo.error'),
)


urlpatterns = patterns('',
    url(r'^robots.txt$', views.robots, name='robots.txt'),
    ('^services', include(services_patterns)),

    url('^locales$', views.locales, name='sumo.locales'),

    # Shortcuts:
    url('^contribute/?$', RedirectView.as_view(url='/kb/superheroes-wanted',
                                               permanent=False)),
    url(r'^windows7-support(?:\\/)?$',
        RedirectView.as_view(url='/home/?as=u', permanent=False)),
)


if 'django_qunit' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^qunit/(?P<path>.*)', views.kitsune_qunit),
        url(r'^_qunit/', include('django_qunit.urls')),
    )
