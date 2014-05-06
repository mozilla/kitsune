from django.conf.urls import patterns, url


urlpatterns = patterns(
    'kitsune.community.views',
    url(r'^/contributor_results$', 'contributor_results', name='community.contributor_results'),
    url(r'^/view_all$', 'view_all', name='community.view_all'),
    url(r'^$', 'home', name='community.home'),
)
