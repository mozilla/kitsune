import logging
from smtplib import SMTPException

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User

from statsd import statsd

from kitsune.sumo import email_utils
from kitsune.users import ERROR_SEND_EMAIL
from kitsune.users.forms import RegisterForm, AuthenticationForm
from kitsune.users.models import RegistrationProfile, Group, CONTRIBUTOR_GROUP


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


def handle_register(request, text_template=None, html_template=None,
                    subject=None, email_data=None, *args, **kwargs):
    """Handle to help registration."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form = try_send_email_with_form(
                RegistrationProfile.objects.create_inactive_user,
                form, 'email',
                form.cleaned_data['username'],
                form.cleaned_data['password'],
                form.cleaned_data['email'],
                locale=request.LANGUAGE_CODE,
                text_template=text_template,
                html_template=html_template,
                subject=subject,
                email_data=email_data,
                volunteer_interest=form.cleaned_data['interested'],
                *args, **kwargs)
            if not form.is_valid():
                # Delete user if form is not valid, i.e. email was not sent.
                # This is in a POST request and so always pinned to master,
                # so there is no race condition.
                User.objects.filter(email=form.instance.email).delete()
            else:
                statsd.incr('user.register')
        return form
    return RegisterForm()


def try_send_email_with_form(func, form, field_name, *args, **kwargs):
    """Send an email by calling func, catch SMTPException and place errors in
    form."""
    try:
        func(*args, **kwargs)
    except SMTPException, e:
        log.warning(u'Failed to send email: %s' % e)
        if not 'email' in form.errors:
            form.errors[field_name] = []
        form.errors[field_name].append(unicode(ERROR_SEND_EMAIL))
    return form

def add_to_contributors(request, user):
    group = Group.objects.get(name=CONTRIBUTOR_GROUP)
    user.groups.add(group)
    user.save()

    @email_utils.safe_translation
    def _make_mail(locale):
        mail = email_utils.make_mail(
            subject=_('Welcome to SUMO!'),
            text_template='users/email/contributor.ltxt',
            html_template='users/email/contributor.html',
            context_vars={'username': user.username},
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=user.email)

        return mail

    email_utils.send_messages([_make_mail(request.LANGUAGE_CODE)])
