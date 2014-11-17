from rest_framework import routers
from django.conf.urls import include, patterns, url

from kitsune.users import api


router = routers.SimpleRouter()
router.register(r'user', api.ProfileViewSet, base_name='user')

# API urls
urlpatterns = patterns(
    '',
    url('^1/users/test_auth$', api.test_auth, name='users.test_auth'),
    url('^1/users/get_token$', api.GetToken.as_view(), name='users.get_token'),
    url('^2/user/generate', api.ProfileViewSet.as_view({'post': 'generate'}),
        name='user-generate'),
    url('^2/', include(router.urls)),
)
