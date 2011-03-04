from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to


urlpatterns = patterns('landings.views',
    url(r'^$', redirect_to, {'url': 'home'}),
    url(r'^home$', 'home', name='home'),
    url(r'^mobile$', 'mobile', name='home.mobile'),
    url(r'^sync$', 'sync', name='home.sync'),
    url(r'^firefox-home$', 'fxhome', name='home.fxhome'),
)
