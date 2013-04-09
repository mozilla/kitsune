import logging
from smtplib import SMTPException

from django.contrib import auth
from django.contrib.auth.models import User

from statsd import statsd

from users import ERROR_SEND_EMAIL
from users.forms import RegisterForm, AuthenticationForm
from users.models import RegistrationProfile


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


def handle_register(request, email_text_template=None,
                    email_html_template=None, email_subject=None,
                    email_data=None, *args, **kwargs):
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
                email_text_template=email_text_template,
                email_html_template=email_html_template,
                email_subject=email_subject,
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
