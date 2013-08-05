from django.conf.urls import patterns, url

from kitsune.dashboards import api


urlpatterns = patterns('kitsune.dashboards.views',
    url(r'^localization$', 'localization', name='dashboards.localization'),
    url(r'^contributors$', 'contributors', name='dashboards.contributors'),
    url(r'^wiki-rows/(?P<readout_slug>[^/]+)', 'wiki_rows',
        name='dashboards.wiki_rows'),
    url(r'^localization/(?P<readout_slug>[^/]+)', 'localization_detail',
        name='dashboards.localization_detail'),
    url(r'^contributors/(?P<readout_slug>[^/]+)', 'contributors_detail',
        name='dashboards.contributors_detail'),

    # API for pull wiki metrics data.
    url(r'^api/v1/wikimetrics/?$', api.WikiMetricList.as_view(),
        name='api.wikimetric_list'),
)
