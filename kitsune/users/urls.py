from django.conf.urls import patterns, url, include
from django.contrib.contenttypes.models import ContentType

import kitsune.flagit.views
from kitsune.sumo.views import redirect_to
from kitsune.users import api
from kitsune.users import views
from kitsune.users.models import Profile


# API patterns. All start with /users/api.
api_patterns = patterns('',
    url(r'^usernames', api.usernames, name='users.api.usernames'),
)

# These will all start with /user/<user_id>/
detail_patterns = patterns('',
    url(r'^$', views.profile, name='users.profile'),
    url(r'^/documents$', views.documents_contributed, name='users.documents'),
# TODO:
#    url('^abuse', views.report_abuse, name='users.abuse'),
)

users_patterns = patterns('',
    url(r'^/auth$', views.user_auth, name='users.auth'),
    url(r'^/authcontributor$', views.user_auth, {'contributor': True},
        name='users.auth_contributor'),

    url(r'^/login$', views.login, name='users.login'),
    url(r'^/logout$', views.logout, name='users.logout'),
    url(r'^/register$', views.register, name='users.register'),
    url(r'^/registercontributor$', views.register, {'contributor': True},
        name='users.registercontributor'),

    url(r'^/activate/(?P<activation_key>\w+)$', views.activate,
        name='users.old_activate'),
    url(r'^/activate/(?P<user_id>\d+)/(?P<activation_key>\w+)$',
        views.activate, name='users.activate'),
    url(r'^/edit$', views.edit_profile, name='users.edit_profile'),
    url(r'^/settings$', views.edit_settings, name='users.edit_settings'),
    url(r'^/avatar$', views.edit_avatar, name='users.edit_avatar'),
    url(r'^/avatar/delete$', views.delete_avatar, name='users.delete_avatar'),
    url(r'^/deactivate$', views.deactivate, name='users.deactivate'),
    url(r'^/deactivation_log$', views.deactivation_log,
        name='users.deactivation_log'),
    url(r'^/make_contributor$', views.make_contributor,
        name='users.make_contributor'),

    # Browser ID
    url(r'^/browserid_verify$', views.browserid_verify,
        name='users.browserid_verify'),
    url(r'^/browserid_signup$', views.browserid_signup,
        name='users.browserid_signup'),

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
    (r'^/api/', include(api_patterns)),
)

urlpatterns = patterns('',
    # URLs for a single user.
    (r'^user/(?P<user_id>\d+)', include(detail_patterns)),
    url(r'^user/(?P<object_id>\d+)/flag$', kitsune.flagit.views.flag,
        {'content_type': ContentType.objects.get_for_model(Profile).id},
        name='users.flag'),
    (r'^users', include(users_patterns)),
)
