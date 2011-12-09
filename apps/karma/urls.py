from django.conf.urls.defaults import patterns, url, include


api_patterns = patterns('karma.api',
    url(r'^/users$', 'users', name='karma.api.users'),
    url(r'^/overview$', 'overview', name='karma.api.overview'),
    url(r'^/details$', 'details', name='karma.api.details'),
)


urlpatterns = patterns('karma.views',
    url(r'^/questions$', 'questions_dashboard',
        name='karma.questions_dashboard'),
    (r'^/api', include(api_patterns)),
)
