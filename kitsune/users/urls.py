from django.conf import settings
from django.conf.urls import include, url
from django.views.decorators.cache import never_cache

import kitsune.flagit.views
from kitsune.users import api, views
from kitsune.users.models import Profile

# API patterns. All start with /users/api.
api_patterns = [
    url(r"^usernames", api.usernames, name="users.api.usernames"),
]

# These will all start with /user/<user_id>/
detail_patterns = [
    url(r"^$", views.profile, name="users.profile"),
    url(r"^/questions$", views.questions_contributed, name="users.questions"),
    url(r"^/answers$", views.answers_contributed, name="users.answers"),
    url(r"^/documents$", views.documents_contributed, name="users.documents"),
    url(r"^/edit$", views.edit_profile, name="users.edit_profile"),
    url(r"^/subscriptions$", views.subscribed_products, name="users.subscriptions"),
]

if settings.DEV and settings.ENABLE_DEV_LOGIN:
    detail_patterns += [
        url(r"^/become$", views.become, name="users.become"),
    ]

users_patterns = [
    url(r"^/auth$", views.user_auth, name="users.auth"),
    url(r"^/login$", views.login, name="users.login"),
    url(r"^/logout$", views.logout, name="users.logout"),
    url(r"^/close_account$", views.close_account, name="users.close_account"),
    url(r"^/edit$", views.edit_profile, name="users.edit_my_profile"),
    url(r"^/settings$", views.edit_settings, name="users.edit_settings"),
    url(r"^/contributions$", views.edit_contribution_area, name="users.edit_contribution_area"),
    url(r"^/watches$", views.edit_watch_list, name="users.edit_watch_list"),
    url(r"^/deactivate$", views.deactivate, name="users.deactivate"),
    url(
        r"^/deactivate-spam$", views.deactivate, {"mark_spam": True}, name="users.deactivate-spam"
    ),
    url(r"^/deactivation_log$", views.deactivation_log, name="users.deactivation_log"),
    url(r"^/make_contributor$", views.make_contributor, name="users.make_contributor"),
    url(r"^/api/", include(api_patterns)),
]

urlpatterns = [
    # URLs for a single user.
    url(r"^user/(?P<username>[\w@\.\s+-]+)", include(detail_patterns)),
    url(
        r"^user/(?P<object_id>\w+)/flag$",
        kitsune.flagit.views.flag,
        {"model": Profile},
        name="users.flag",
    ),
    url(r"^users", include(users_patterns)),
]


if settings.OIDC_ENABLE:
    urlpatterns += [
        url(
            r"^fxa/callback/$",
            never_cache(views.FXAAuthenticationCallbackView.as_view()),
            name="users.fxa_authentication_callback",
        ),
        url(
            r"^fxa/authenticate/$",
            never_cache(views.FXAAuthenticateView.as_view()),
            name="users.fxa_authentication_init",
        ),
        url(
            r"^fxa/logout/$",
            never_cache(views.FXALogoutView.as_view()),
            name="users.fxa_logout_url",
        ),
        url(r"^fxa/events/?$", never_cache(views.WebhookView.as_view()), name="users.fxa_webhook"),
        url(r"^oidc/", include("mozilla_django_oidc.urls")),
    ]
