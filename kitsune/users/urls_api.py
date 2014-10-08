from rest_framework import routers
from django.conf.urls import include, patterns, url

from kitsune.users import api


router = routers.SimpleRouter()
router.register(r'user', api.ProfileViewSet, base_name='user')

# API urls
urlpatterns = patterns(
    '',
    url('^1/users/test_auth$', api.test_auth),
    url('^1/users/get_token$',
        'rest_framework.authtoken.views.obtain_auth_token'),
    url('^2/', include(router.urls)),
)
