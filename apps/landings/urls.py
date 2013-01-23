from django.conf.urls.defaults import patterns, url

from sumo.views import redirect_to


urlpatterns = patterns('landings.views',
    url(r'^$', 'desktop_or_mobile', name='home.default'),
    url(r'^home$', 'home', name='home'),

    # Redirect from old mobile URL to new one.
    url(r'^mobile$', redirect_to,
        {'url': 'products.product', 'slug': 'mobile'}, name='home.mobile'),

    # A static page for downloading FirefoxIntegrityCheck.exe
    url(r'^download-firefox-integrity-check$', 'integrity_check',
        name='download.integrity-check'),
)
