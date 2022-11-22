from django.urls import include, re_path
from rest_framework import routers

from kitsune.users import api

router = routers.SimpleRouter()
router.register(r"user", api.ProfileViewSet, basename="user")

# API urls
urlpatterns = [
    re_path("^1/users/test_auth$", api.test_auth, name="users.test_auth"),
    re_path(
        "^2/user/weekly-solutions",
        api.ProfileViewSet.as_view({"get": "weekly_solutions"}),
        name="user-weekly-solutions",
    ),
    re_path("^2/", include(router.urls)),
]
