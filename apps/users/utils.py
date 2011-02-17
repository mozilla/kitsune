import logging
from smtplib import SMTPException

from django.contrib import auth

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

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

        return form

    request.session.set_test_cookie()
    return AuthenticationForm()


def handle_register(request):
    """Handle to help registration."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form = try_send_email_with_form(
                RegistrationProfile.objects.create_inactive_user,
                form, 'email',
                form.cleaned_data['username'],
                form.cleaned_data['password'],
                form.cleaned_data['email'])
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
