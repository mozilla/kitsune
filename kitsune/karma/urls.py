from django.conf.urls import patterns, url, include


api_patterns = patterns('kitsune.karma.api',
    url(r'^/users$', 'users', name='karma.api.users'),
    url(r'^/overview$', 'overview', name='karma.api.overview'),
    url(r'^/details$', 'details', name='karma.api.details'),
)


urlpatterns = patterns('kitsune.karma.views',
    url(r'^/questions$', 'questions_dashboard',
        name='karma.questions_dashboard'),
    (r'^/api', include(api_patterns)),
)
