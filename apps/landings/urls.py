from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('landings.views',
    url(r'^$', 'desktop_or_mobile', name='home.default'),
    url(r'^home$', 'home', name='home'),

    # A static page for downloading FirefoxIntegrityCheck.exe
    url(r'^download-firefox-integrity-check$', 'integrity_check',
        name='download.integrity-check'),
)
