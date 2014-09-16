from django.conf.urls import include, patterns, url
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.i18n import javascript_catalog
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView

import authority
import badger
from adminplus.sites import AdminSitePlus
from waffle.views import wafflejs


admin.site = AdminSitePlus()
admin.autodiscover()
admin.site.login = login_required(admin.site.login)
authority.autodiscover()
badger.autodiscover()


urlpatterns = patterns(
    '',
    (r'^search', include('kitsune.search.urls')),
    (r'^forums', include('kitsune.forums.urls')),
    (r'^questions', include('kitsune.questions.urls')),
    (r'^flagged', include('kitsune.flagit.urls')),
    (r'^upload', include('kitsune.upload.urls')),
    (r'^kb', include('kitsune.wiki.urls')),
    (r'^gallery', include('kitsune.gallery.urls')),
    (r'^army-of-awesome', include('kitsune.customercare.urls')),
    (r'^chat', RedirectView.as_view(url='questions/new')),
    (r'^messages', include('kitsune.messages.urls')),
    (r'^1', include('kitsune.inproduct.urls')),
    (r'^postcrash', include('kitsune.postcrash.urls')),
    (r'^groups', include('kitsune.groups.urls')),
    (r'^karma', include('kitsune.karma.urls')),
    (r'^kpi/', include('kitsune.kpi.urls')),
    (r'^products', include('kitsune.products.urls')),
    (r'^announcements', include('kitsune.announcements.urls')),
    (r'^community', include('kitsune.community.urls')),
    (r'^badges/', include('kitsune.kbadge.urls')),
    (r'^offline', include('kitsune.offline.urls')),

    # Kitsune admin (not Django admin).
    (r'^admin/', include(admin.site.urls)),

    # Javascript translations.
    url(r'^jsi18n/.*$', cache_page(60 * 60 * 24 * 365)(javascript_catalog),
        {'domain': 'javascript', 'packages': ['kitsune']}, name='jsi18n'),
    # Yaocho translations. These don't need cached because Yaocho downloads
    # them in a build step, not on the client.
    url(r'^jsi18n-yaocho/.*$', javascript_catalog,
        {'domain': 'yaocho', 'packages': ['kitsune']}, name='jsi18n-yaocho'),
    # JavaScript Waffle.
    url(r'^wafflejs$', wafflejs, name='wafflejs'),

    (r'^', include('kitsune.dashboards.urls')),
    (r'^', include('kitsune.landings.urls')),
    (r'^', include('tidings.urls')),  # Keep short for email wrapping.
    (r'^', include('kitsune.kpi.urls_api')),

    # Users
    ('', include('kitsune.users.urls')),

    # Services and sundry.
    (r'', include('kitsune.sumo.urls')),

    # APIs
    (r'^api/1/kb/', include('kitsune.wiki.urls_api')),
    (r'^api/1/products/', include('kitsune.products.urls_api')),
    (r'^api/1/customercare/', include('kitsune.customercare.urls_api')),
    (r'^api/1/gallery/', include('kitsune.gallery.urls_api')),
    (r'^api/1/users/', include('kitsune.users.urls_api')),
)

# Handle 404 and 500 errors
handler404 = 'kitsune.sumo.views.handle404'
handler500 = 'kitsune.sumo.views.handle500'

if settings.DEBUG:
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns(
        '',
        (r'^%s/(?P<path>.*)$' % media_url, 'kitsune.sumo.views.serve_cors',
         {'document_root': settings.MEDIA_ROOT}),
    )
