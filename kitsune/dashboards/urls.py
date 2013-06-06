from django.conf.urls import patterns, url


urlpatterns = patterns('kitsune.dashboards.views',
    url(r'^dashboard$', 'default_dashboard', name='dashboards.default'),
    url(r'^dashboard/(?P<group_id>\d+)$', 'group_dashboard',
        name='dashboards.group'),
    url(r'^localization$', 'localization', name='dashboards.localization'),
    url(r'^contributors$', 'contributors', name='dashboards.contributors'),
    url(r'^wiki-rows/(?P<readout_slug>[^/]+)', 'wiki_rows',
        name='dashboards.wiki_rows'),
    url(r'^localization/(?P<readout_slug>[^/]+)', 'localization_detail',
        name='dashboards.localization_detail'),
    url(r'^contributors/(?P<readout_slug>[^/]+)', 'contributors_detail',
        name='dashboards.contributors_detail'),
)
