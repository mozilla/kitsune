from django.conf.urls import patterns, url


urlpatterns = patterns(
    'kitsune.kpi.views',
    url(r'^dashboard$', 'dashboard', name='kpi.dashboard'),
)
