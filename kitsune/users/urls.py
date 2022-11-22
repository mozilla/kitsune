from django.conf import settings
from django.urls import include, re_path
from django.views.decorators.cache import never_cache

import kitsune.flagit.views
from kitsune.users import api, views
from kitsune.users.models import Profile

# API patterns. All start with /users/api.
api_patterns = [
    re_path(r"^usernames", api.usernames, name="users.api.usernames"),
]

# These will all start with /user/<user_id>/
detail_patterns = [
    re_path(r"^$", views.profile, name="users.profile"),
    re_path(r"^/questions$", views.questions_contributed, name="users.questions"),
    re_path(r"^/answers$", views.answers_contributed, name="users.answers"),
    re_path(r"^/documents$", views.documents_contributed, name="users.documents"),
    re_path(r"^/edit$", views.edit_profile, name="users.edit_profile"),
    re_path(r"^/subscriptions$", views.subscribed_products, name="users.subscriptions"),
]

if settings.DEV and settings.ENABLE_DEV_LOGIN:
    detail_patterns += [
        re_path(r"^/become$", views.become, name="users.become"),
    ]

users_patterns = [
    re_path(r"^/auth$", views.user_auth, name="users.auth"),
    re_path(r"^/login$", views.login, name="users.login"),
    re_path(r"^/logout$", views.logout, name="users.logout"),
    re_path(r"^/close_account$", views.close_account, name="users.close_account"),
    re_path(r"^/edit$", views.edit_profile, name="users.edit_my_profile"),
    re_path(r"^/settings$", views.edit_settings, name="users.edit_settings"),
    re_path(
        r"^/contributions$", views.edit_contribution_area, name="users.edit_contribution_area"
    ),
    re_path(r"^/watches$", views.edit_watch_list, name="users.edit_watch_list"),
    re_path(r"^/deactivate$", views.deactivate, name="users.deactivate"),
    re_path(
        r"^/deactivate-spam$", views.deactivate, {"mark_spam": True}, name="users.deactivate-spam"
    ),
    re_path(r"^/deactivation_log$", views.deactivation_log, name="users.deactivation_log"),
    re_path(r"^/make_contributor$", views.make_contributor, name="users.make_contributor"),
    re_path(r"^/api/", include(api_patterns)),
]

urlpatterns = [
    # URLs for a single user.
    re_path(r"^user/(?P<username>[\w@\.\s+-]+)", include(detail_patterns)),
    re_path(
        r"^user/(?P<object_id>\w+)/flag$",
        kitsune.flagit.views.flag,
        {"model": Profile},
        name="users.flag",
    ),
    re_path(r"^users", include(users_patterns)),
]


if settings.OIDC_ENABLE:
    urlpatterns += [
        re_path(
            r"^fxa/callback/$",
            never_cache(views.FXAAuthenticationCallbackView.as_view()),
            name="users.fxa_authentication_callback",
        ),
        re_path(
            r"^fxa/authenticate/$",
            never_cache(views.FXAAuthenticateView.as_view()),
            name="users.fxa_authentication_init",
        ),
        re_path(
            r"^fxa/logout/$",
            never_cache(views.FXALogoutView.as_view()),
            name="users.fxa_logout_url",
        ),
        re_path(
            r"^fxa/events/?$", never_cache(views.WebhookView.as_view()), name="users.fxa_webhook"
        ),
        re_path(r"^oidc/", include("mozilla_django_oidc.urls")),
    ]
