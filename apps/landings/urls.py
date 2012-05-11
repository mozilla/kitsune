from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('landings.views',
    url(r'^$', 'desktop_or_mobile', name='home.default'),
    url(r'^home$', 'home', name='home'),
    url(r'^mobile$', 'mobile', name='home.mobile'),
    url(r'^sync$', 'sync', name='home.sync'),
    url(r'^firefox-home$', 'fxhome', name='home.fxhome'),
    url(r'^marketplace$', 'marketplace', name='home.marketplace'),
    url(r'^firefox$', 'firefox', name='home.firefox'),
    url(r'^products$', 'products', name='home.products'),
    url(r'^kb$', 'kb', name='home.kb'),
    url(r'^ask$', 'ask', name='home.ask'),
    url(r'^participate$', 'participate', name='home.participate'),
    url(r'^feedback$', 'feedback', name='home.feedback'),

    # Special landing page for MozCamp
    url(r'^reminder$', 'reminder', name='home.reminder'),

    # A static page for downloading FirefoxIntegrityCheck.exe
    url(r'^download-firefox-integrity-check$', 'integrity_check',
        name='download.integrity-check'),
)
