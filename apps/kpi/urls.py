from django.conf.urls.defaults import patterns, url, include

api_patterns = patterns('kpi.api',
    url(r'^/percent_answered$', 'percent_answered', name='karma.api.percent_answered'),
)

urlpatterns = patterns('kpi.views',
    url(r'^/dashboard$', 'dashboard',
        name='kpi.dashboard'),
    (r'^/api', include(api_patterns)),
)
