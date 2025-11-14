from django.urls import include, path, re_path
from django.views.decorators.cache import never_cache
from sentry_sdk import capture_exception

from kitsune.users import views

real_fxa_callback = views.FXAAuthenticationCallbackView.as_view()


def fxa_callback_wrapper(request, *args, **kwargs):
    try:
        return real_fxa_callback(request, *args, **kwargs)
    except Exception as err:
        capture_exception(err)
        raise err


urlpatterns = [
    path(
        "fxa/callback/",
        never_cache(fxa_callback_wrapper),
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
