import bisect
import logging
from smtplib import SMTPException

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from django_statsd.clients import statsd

from kitsune.sumo import email_utils
from kitsune.users import ERROR_SEND_EMAIL
from kitsune.users.forms import AuthenticationForm
from kitsune.users.models import Group, CONTRIBUTOR_GROUP, Deactivation


log = logging.getLogger('k.users')


def handle_login(request, only_active=True):
    auth.logout(request)

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST, only_active=only_active)
        if form.is_valid():
            auth.login(request, form.get_user())
            statsd.incr('user.login')

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

        return form

    request.session.set_test_cookie()
    return AuthenticationForm()


def try_send_email_with_form(func, form, field_name, *args, **kwargs):
    """Send an email by calling func, catch SMTPException and place errors in
    form."""
    try:
        func(*args, **kwargs)
    except SMTPException as e:
        log.warning(u'Failed to send email: %s' % e)
        if 'email' not in form.errors:
            form.errors[field_name] = []
        form.errors[field_name].append(unicode(ERROR_SEND_EMAIL))
    return form


def add_to_contributors(user, language_code):
    group = Group.objects.get(name=CONTRIBUTOR_GROUP)
    user.groups.add(group)
    user.save()

    @email_utils.safe_translation
    def _make_mail(locale):
        mail = email_utils.make_mail(
            subject=_('Welcome to SUMO!'),
            text_template='users/email/contributor.ltxt',
            html_template='users/email/contributor.html',
            context_vars={'contributor': user},
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=user.email)

        return mail

    email_utils.send_messages([_make_mail(language_code)])


def suggest_username(email):
    username = email.split('@', 1)[0]

    username_regex = r'^{0}[0-9]*$'.format(username)
    users = User.objects.filter(username__iregex=username_regex)

    if users.count() > 0:
        ids = []
        for user in users:
            # get the number at the end
            i = user.username[len(username):]

            # in case there's no number in the case where just the base is taken
            if i:
                i = int(i)
                bisect.insort(ids, i)
            else:
                ids.insert(0, 0)

        for index, i in enumerate(ids):
            if index + 1 < len(ids):
                suggested_number = i + 1
                # let's check if the number exists. Username can have leading zeroes
                # which translates to an array [0, 1, 1, 2]. Without the membership
                # check this snippet will return 2 which is wrong
                if suggested_number != ids[index + 1] and suggested_number not in ids:
                    break

        username = '{0}{1}'.format(username, i + 1)

    return username


def deactivate_user(user, moderator):
    user.is_active = False
    user.save()
    deactivation = Deactivation(user=user, moderator=moderator)
    deactivation.save()


def get_oidc_fxa_setting(attr):
    """Helper method to return the appropriate setting for Firefox Accounts authentication."""
    FXA_CONFIGURATION = {
        'OIDC_OP_TOKEN_ENDPOINT': settings.FXA_OP_TOKEN_ENDPOINT,
        'OIDC_OP_AUTHORIZATION_ENDPOINT': settings.FXA_OP_AUTHORIZATION_ENDPOINT,
        'OIDC_OP_USER_ENDPOINT': settings.FXA_OP_USER_ENDPOINT,
        'OIDC_OP_JWKS_ENDPOINT': settings.FXA_OP_JWKS_ENDPOINT,
        'OIDC_RP_CLIENT_ID': settings.FXA_RP_CLIENT_ID,
        'OIDC_RP_CLIENT_SECRET': settings.FXA_RP_CLIENT_SECRET,
        'OIDC_AUTHENTICATION_CALLBACK_URL': 'users.fxa_authentication_callback',
        'OIDC_CREATE_USER': settings.FXA_CREATE_USER,
        'OIDC_RP_SIGN_ALGO': settings.FXA_RP_SIGN_ALGO,
        'OIDC_USE_NONCE': settings.FXA_USE_NONCE,
        'OIDC_RP_SCOPES': settings.FXA_RP_SCOPES,
        'LOGOUT_REDIRECT_URL': settings.FXA_LOGOUT_REDIRECT_URL,
        'OIDC_USERNAME_ALGO': settings.FXA_USERNAME_ALGO,
        'OIDC_STORE_ACCESS_TOKEN': settings.FXA_STORE_ACCESS_TOKEN
    }

    return FXA_CONFIGURATION.get(attr, None)
