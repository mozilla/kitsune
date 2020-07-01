from django.conf.urls import include
from django.conf.urls import url
from rest_framework import routers

from kitsune.users import api

router = routers.SimpleRouter()
router.register(r"user", api.ProfileViewSet, basename="user")

# API urls
urlpatterns = [
    url("^1/users/test_auth$", api.test_auth, name="users.test_auth"),
    url(
        "^2/user/weekly-solutions",
        api.ProfileViewSet.as_view({"get": "weekly_solutions"}),
        name="user-weekly-solutions",
    ),
    url("^2/", include(router.urls)),
]
