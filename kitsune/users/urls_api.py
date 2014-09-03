from django.conf.urls import patterns, url

from kitsune.users import api


# API urls
urlpatterns = patterns(
    '',
    url('^test_auth$', api.test_auth),
    url('^get_token$', 'rest_framework.authtoken.views.obtain_auth_token'),
)
