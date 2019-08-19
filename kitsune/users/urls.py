from django.conf import settings
from django.conf.urls import include, url
from django.views.decorators.cache import never_cache

from mozilla_django_oidc.views import OIDCAuthenticationCallbackView

import kitsune.flagit.views
from kitsune.sumo.views import redirect_to
from kitsune.users import api, views
from kitsune.users.models import Profile


# API patterns. All start with /users/api.
api_patterns = [
    url(r'^usernames', api.usernames, name='users.api.usernames'),
]

# These will all start with /user/<user_id>/
detail_patterns = [
    url(r'^$', views.profile, name='users.profile'),
    url(r'^/documents$', views.documents_contributed, name='users.documents'),
    url(r'^/edit$', views.edit_profile, name='users.edit_profile'),
    # TODO:
    # url('^abuse', views.report_abuse, name='users.abuse'),
]

users_patterns = [
    url(r'^/auth$', views.user_auth, name='users.auth'),

    url(r'^/login$', views.login, name='users.login'),
    url(r'^/logout$', views.logout, name='users.logout'),
    url(r'^/close_account$', views.close_account, name='users.close_account'),

    url(r'^/activate/(?P<activation_key>\w+)$', views.activate,
        name='users.old_activate'),
    url(r'^/activate/(?P<user_id>\d+)/(?P<activation_key>\w+)$',
        views.activate, name='users.activate'),
    url(r'^/edit$', views.edit_profile, name='users.edit_my_profile'),
    url(r'^/settings$', views.edit_settings, name='users.edit_settings'),
    url(r'^/watches$', views.edit_watch_list, name='users.edit_watch_list'),
    url(r'^/avatar$', views.edit_avatar, name='users.edit_avatar'),
    url(r'^/avatar/delete$', views.delete_avatar, name='users.delete_avatar'),
    url(r'^/deactivate$', views.deactivate, name='users.deactivate'),
    url(r'^/deactivate-spam$', views.deactivate, {'mark_spam': True},
        name='users.deactivate-spam'),
    url(r'^/deactivation_log$', views.deactivation_log,
        name='users.deactivation_log'),
    url(r'^/make_contributor$', views.make_contributor,
        name='users.make_contributor'),

    # Password reset
    url(r'^/pwreset$', views.password_reset, name='users.pw_reset'),
    url(r'^/pwresetsent$', views.password_reset_sent,
        name='users.pw_reset_sent'),
    url(r'^/pwreset/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)$',
        views.password_reset_confirm, name="users.pw_reset_confirm"),
    url(r'^/pwresetcomplete$', views.password_reset_complete,
        name="users.pw_reset_complete"),

    # Forgot username
    url(r'^/forgot-username$', views.forgot_username,
        name='users.forgot_username'),

    # Change password
    url(r'^/pwchange$', views.password_change, name='users.pw_change'),
    url(r'^/pwchangecomplete$', views.password_change_complete,
        name='users.pw_change_complete'),

    url(r'^/resendconfirmation$', views.resend_confirmation,
        name='users.resend_confirmation'),

    # Change email
    url(r'^change_email$', redirect_to, {'url': 'users.change_email'},
        name='users.old_change_email'),
    url(r'^confirm_email/(?P<activation_key>\w+)$',
        redirect_to, {'url': 'users.confirm_email'},
        name='users.old_confirm_email'),
    url(r'^/change_email$', views.change_email, name='users.change_email'),
    url(r'^/confirm_email/(?P<activation_key>\w+)$',
        views.confirm_change_email, name='users.confirm_email'),
    url(r'^/api/', include(api_patterns)),
]

urlpatterns = [
    # URLs for a single user.
    url(r'^user/(?P<username>[\w@\.\s+-]+)', include(detail_patterns)),
    url(r'^user/(?P<object_id>\w+)/flag$', kitsune.flagit.views.flag,
        {'model': Profile}, name='users.flag'),
    url(r'^users', include(users_patterns)),
]


if settings.OIDC_ENABLE:
    urlpatterns += [
        url(r'^fxa/callback/$', never_cache(OIDCAuthenticationCallbackView.as_view()),
            name='users.fxa_authentication_callback'),
        url(r'^fxa/authenticate/$', never_cache(views.FXAAuthenticateView.as_view()),
            name='users.fxa_authentication_init'),
        url(r'^fxa/logout/$', never_cache(views.FXALogoutView.as_view()),
            name='users.fxa_logout_url'),
        url(r'^oidc/', include('mozilla_django_oidc.urls')),
    ]
