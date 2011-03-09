from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to


urlpatterns = patterns('dashboards.views',
    url(r'^dashboard$', redirect_to, {'url': 'dashboard/forums'}),
    url(r'^dashboard/forums$', 'review', name='dashboards.review'),
    url(r'^dashboard/questions$', 'questions', name='dashboards.questions'),
    url(r'^localization$', 'localization', name='dashboards.localization'),
    url(r'^contributors$', 'contributors', name='dashboards.contributors'),
    url(r'^wiki-rows/(?P<readout_slug>[^/]+)', 'wiki_rows',
        name='dashboards.wiki_rows'),
    url(r'^localization/(?P<readout_slug>[^/]+)', 'localization_detail',
        name='dashboards.localization_detail'),
    url(r'^contributors/(?P<readout_slug>[^/]+)', 'contributors_detail',
        name='dashboards.contributors_detail'),
)
