from django.conf.urls.defaults import include, patterns, url
from django.conf import settings
from django.contrib import admin
from django.views.i18n import javascript_catalog
from django.views.decorators.cache import cache_page

from adminplus import AdminSitePlus
import authority
from waffle.views import wafflejs


admin.site = AdminSitePlus()
admin.autodiscover()
authority.autodiscover()

urlpatterns = patterns('',
    (r'^search', include('search.urls')),
    (r'^forums', include('forums.urls')),
    (r'^questions', include('questions.urls')),
    (r'^flagged', include('flagit.urls')),
    (r'^upload', include('upload.urls')),
    (r'^kb', include('wiki.urls')),
    (r'^gallery', include('gallery.urls')),
    (r'^army-of-awesome', include('customercare.urls')),
    (r'^chat', include('chat.urls')),
    (r'^messages', include('messages.urls')),
    (r'^1', include('inproduct.urls')),
    (r'^postcrash', include('postcrash.urls')),
    (r'^groups', include('groups.urls')),

    # Kitsune admin (not Django admin).
    (r'^admin/', include(admin.site.urls)),

    # Javascript translations.
    url(r'^jsi18n/.*$', cache_page(60 * 60 * 24 * 365)(javascript_catalog),
        {'domain': 'javascript', 'packages': ['kitsune']}, name='jsi18n'),
    # JavaScript Waffle.
    url(r'^wafflejs$', wafflejs, name='wafflejs'),

    (r'^', include('dashboards.urls')),
    (r'^', include('landings.urls')),
    (r'^', include('tidings.urls')),  # Keep short for email wrapping.

    # Users
    ('', include('users.urls')),

    # Services and sundry.
    (r'', include('sumo.urls')),
)

# Handle 404 and 500 errors
handler404 = 'sumo.views.handle404'
handler500 = 'sumo.views.handle500'

if settings.DEBUG:
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
          {'document_root': settings.MEDIA_ROOT}),
    )
