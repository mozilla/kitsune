from django.conf.urls.defaults import patterns, url

from sumo.views import redirect_to


urlpatterns = patterns('landings.views',
    url(r'^$', redirect_to, {'url': 'home'}, name='home.default'),
    url(r'^home$', 'home', name='home'),
    url(r'^mobile$', 'mobile', name='home.mobile'),
    url(r'^sync$', 'sync', name='home.sync'),
    url(r'^firefox-home$', 'fxhome', name='home.fxhome'),

    # A static page for downloading FirefoxIntegrityCheck.exe
    url(r'^download-firefox-integrity-check$', 'integrity_check',
        name='download.integrity-check'),
)
