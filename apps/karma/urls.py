from django.conf.urls.defaults import patterns, url, include


api_patterns = patterns('karma.api',
    url(r'^/users$', 'users', name='karma.api.users'),
)


urlpatterns = patterns('karma.views',
    url(r'^/questions$', 'questions_dashboard',
        name='karma.questions_dashboard'),
    (r'^/api', include(api_patterns)),
)
