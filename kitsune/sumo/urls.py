from django.conf.urls import patterns, url, include
from django.views.generic.base import RedirectView

from kitsune.sumo import views


services_patterns = patterns(
    '',
    url('^/monitor$', views.monitor, name='sumo.monitor'),
    url('^/version$', views.version_check, name='sumo.version'),
    url('^/error$', views.error, name='sumo.error'),
)


urlpatterns = patterns(
    '',
    url(r'^robots.txt$', views.robots, name='robots.txt'),
    ('^services', include(services_patterns)),

    url('^locales$', views.locales, name='sumo.locales'),
    url('^geoip-suggestion$', views.geoip_suggestion,
        name='sumo.geoip_suggestion'),
    url('^healthz/$', views.liveness, name='sumo.liveness'),
    url('^readiness/$', views.readiness, name='sumo.readiness'),

    # Shortcuts:
    url('^contribute/?$', RedirectView.as_view(url='/get-involved',
                                               permanent=False)),
    url(r'^windows7-support(?:\\/)?$',
        RedirectView.as_view(url='/home/?as=u', permanent=False)),
)
