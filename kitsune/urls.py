from django.conf.urls import include, url
from django.conf import settings
from django.views.i18n import javascript_catalog
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView
from django.views.static import serve as servestatic

import authority
from waffle.views import wafflejs

from kitsune.sumo import views as sumo_views
# Note: This must come before importing admin because it patches the
# admin.
from kitsune.sumo.monkeypatch import patch
patch()

from django.contrib import admin  # noqa
admin.autodiscover()

authority.autodiscover()

urlpatterns = [
    url(r'^search', include('kitsune.search.urls')),
    url(r'^forums', include('kitsune.forums.urls')),
    url(r'^questions', include('kitsune.questions.urls')),
    url(r'^flagged', include('kitsune.flagit.urls')),
    url(r'^upload', include('kitsune.upload.urls')),
    url(r'^kb', include('kitsune.wiki.urls')),
    url(r'^gallery', include('kitsune.gallery.urls')),
    url(r'^chat', RedirectView.as_view(url='questions/new')),
    url(r'^messages', include('kitsune.messages.urls')),
    url(r'^1', include('kitsune.inproduct.urls')),
    url(r'^postcrash', include('kitsune.postcrash.urls')),
    url(r'^groups', include('kitsune.groups.urls')),
    url(r'^kpi/', include('kitsune.kpi.urls')),
    url(r'^products', include('kitsune.products.urls')),
    url(r'^announcements', include('kitsune.announcements.urls')),
    url(r'^community', include('kitsune.community.urls')),
    url(r'^badges/', include('kitsune.kbadge.urls')),

    # Javascript translations.
    url(r'^jsi18n/.*$', cache_page(60 * 60 * 24 * 365)(javascript_catalog),
        {'domain': 'djangojs', 'packages': ['kitsune']}, name='jsi18n'),
    # App translations. These don't need cached because they are downloaded
    # in a build step, not on the client.
    url(r'^jsi18n-yaocho/.*$', javascript_catalog,
        {'domain': 'yaocho', 'packages': ['kitsune']}, name='jsi18n-yaocho'),
    url(r'^jsi18n-buddyup/.*$', javascript_catalog,
        {'domain': 'buddyup', 'packages': ['kitsune']}, name='jsi18n-buddyup'),
    # JavaScript Waffle.
    url(r'^wafflejs$', wafflejs, name='wafflejs'),

    url(r'^', include('kitsune.dashboards.urls')),
    url(r'^', include('kitsune.landings.urls')),
    url(r'^', include('kitsune.kpi.urls_api')),
    url(r'^', include('kitsune.motidings.urls')),

    # Users
    url('', include('kitsune.users.urls')),

    # Services and sundry.
    url(r'', include('kitsune.sumo.urls')),

    # v1 APIs
    url(r'^api/1/kb/', include('kitsune.wiki.urls_api')),
    url(r'^api/1/products/', include('kitsune.products.urls_api')),
    url(r'^api/1/customercare/', include('kitsune.customercare.urls_api')),
    url(r'^api/1/gallery/', include('kitsune.gallery.urls_api')),
    url(r'^api/1/users/', include('kitsune.users.urls_api')),

    # v2 APIs
    url(r'^api/2/', include('kitsune.notifications.urls_api')),
    url(r'^api/2/', include('kitsune.questions.urls_api')),
    url(r'^api/2/', include('kitsune.search.urls_api')),
    url(r'^api/2/', include('kitsune.community.urls_api')),
    url(r'^api/2/', include('kitsune.sumo.urls_api')),

    # These API urls include both v1 and v2 urls.
    url(r'^api/', include('kitsune.users.urls_api')),

    # contribute.json url
    url(r'^(?P<path>contribute\.json)$', servestatic, kwargs={'document_root': settings.ROOT}),
]

# Handle 404 and 500 errors
handler404 = 'kitsune.sumo.views.handle404'
handler500 = 'kitsune.sumo.views.handle500'

if settings.DEBUG:
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += [
        url(r'^%s/(?P<path>.*)$' % media_url, sumo_views.serve_cors,
            {'document_root': settings.MEDIA_ROOT}),
    ]


if settings.ENABLE_ADMIN:
    urlpatterns += [
        url(r'^admin/', include(admin.site.urls)),
    ]
elif settings.ADMIN_REDIRECT_URL:
    urlpatterns.append(
         url(r'^admin/', RedirectView.as_view(url=settings.ADMIN_REDIRECT_URL))
     )
