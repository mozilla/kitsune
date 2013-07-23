from django.conf.urls import patterns, url


urlpatterns = patterns('kitsune.dashboards.views',
    url(r'^localization$', 'localization', name='dashboards.localization'),
    url(r'^localization/(?P<locale_code>[^/]+)$', 'localization',
        name='dashboards.localization_with_locale'),
    url(r'^contributors$', 'contributors', name='dashboards.contributors'),
    url(r'^wiki-rows/(?P<readout_slug>[^/]+)', 'wiki_rows',
        name='dashboards.wiki_rows'),
    url(r'^localization/readout/(?P<readout_slug>[^/]+)',
        'localization_detail', name='dashboards.localization_detail'),
    url(r'^localization/(?P<locale_code>[^/]+)/readout/'
         '(?P<readout_slug>[^/]+)', 'localization_detail',
        name='dashboards.localization_detail_with_locale'),
    url(r'^contributors/readout/(?P<readout_slug>[^/]+)',
        'contributors_detail', name='dashboards.contributors_detail'),
)
