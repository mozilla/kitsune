from django.urls import include, path, re_path
from django.views.decorators.cache import never_cache

from kitsune.users import views


urlpatterns = [
    path(
        "fxa/callback/",
        never_cache(views.FXAAuthenticationCallbackView.as_view()),
        name="users.fxa_authentication_callback",
    ),
    path(
        "fxa/authenticate/",
        never_cache(views.FXAAuthenticateView.as_view()),
        name="users.fxa_authentication_init",
    ),
    path(
        "fxa/logout/",
        never_cache(views.FXALogoutView.as_view()),
        name="users.fxa_logout_url",
    ),
    re_path(r"fxa/events/?$", never_cache(views.WebhookView.as_view()), name="users.fxa_webhook"),
    path("oidc/", include("mozilla_django_oidc.urls")),
]
