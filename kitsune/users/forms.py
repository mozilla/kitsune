import re
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, forms as auth_forms
from django.contrib.auth.forms import (PasswordResetForm as
                                       DjangoPasswordResetForm)
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.core.cache import cache
from django.utils.http import int_to_base36
from django.utils.translation import ugettext as _, ugettext_lazy as _lazy

from kitsune.sumo import email_utils
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.widgets import ImageWidget
from kitsune.upload.forms import clean_image_extension
from kitsune.upload.utils import check_file_size, FileTooLargeError
from kitsune.users.models import Profile
from kitsune.users.widgets import FacebookURLWidget
from kitsune.users.widgets import MonthYearWidget


USERNAME_INVALID = _lazy(u'Username may contain only English letters, '
                         'numbers and ./-/_ characters.')
USERNAME_REQUIRED = _lazy(u'Username is required.')
USERNAME_SHORT = _lazy(u'Username is too short (%(show_value)s characters). '
                       'It must be at least %(limit_value)s characters.')
USERNAME_LONG = _lazy(u'Username is too long (%(show_value)s characters). '
                      'It must be %(limit_value)s characters or less.')
EMAIL_REQUIRED = _lazy(u'Email address is required.')
EMAIL_SHORT = _lazy(u'Email address is too short (%(show_value)s characters). '
                    'It must be at least %(limit_value)s characters.')
EMAIL_LONG = _lazy(u'Email address is too long (%(show_value)s characters). '
                   'It must be %(limit_value)s characters or less.')
PASSWD_REQUIRED = _lazy(u'Password is required.')
PASSWD2_REQUIRED = _lazy(u'Please enter your password twice.')
PASSWD_MIN_LENGTH = 8
PASSWD_MIN_LENGTH_MSG = _lazy('Password must be 8 or more characters.')


# Enforces at least one digit and at least one alpha character.
password_re = re.compile(r'(?=.*\d)(?=.*[a-zA-Z])')


class SettingsForm(forms.Form):
    forums_watch_new_thread = forms.BooleanField(
        required=False, initial=True,
        label=_lazy(u'Watch forum threads I start'))
    forums_watch_after_reply = forms.BooleanField(
        required=False, initial=True,
        label=_lazy(u'Watch forum threads I comment in'))
    kbforums_watch_new_thread = forms.BooleanField(
        required=False, initial=True,
        label=_lazy(u'Watch KB discussion threads I start'))
    kbforums_watch_after_reply = forms.BooleanField(
        required=False, initial=True,
        label=_lazy(u'Watch KB discussion threads I comment in'))
    questions_watch_after_reply = forms.BooleanField(
        required=False, initial=True,
        label=_lazy(u'Watch Question threads I comment in'))
    email_private_messages = forms.BooleanField(
        required=False, initial=True,
        label=_lazy(u'Send emails for private messages'))

    def save_for_user(self, user):
        for field in self.fields.keys():
            value = str(self.cleaned_data[field])
            setting = user.settings.filter(name=field)
            update_count = setting.update(value=value)
            if update_count == 0:
                # This user didn't have this setting so create it.
                user.settings.create(name=field, value=value)


class RegisterForm(forms.ModelForm):
    """A user registration form that requires unique email addresses.

    The default Django user creation form does not require an email address,
    let alone that it be unique. This form does, and sets a minimum length
    for usernames.

    """
    username = forms.RegexField(
        label=_lazy(u'Username:'), max_length=30, min_length=4,
        regex=r'^[\w.-]+$',
        help_text=_lazy(u'Required. 30 characters or fewer. Letters, digits '
                        u'and ./- only.'),
        error_messages={'invalid': USERNAME_INVALID,
                        'required': USERNAME_REQUIRED,
                        'min_length': USERNAME_SHORT,
                        'max_length': USERNAME_LONG})
    email = forms.EmailField(
        label=_lazy(u'Email address:'),
        error_messages={'required': EMAIL_REQUIRED,
                        'min_length': EMAIL_SHORT,
                        'max_length': EMAIL_LONG})
    password = forms.CharField(
        label=_lazy(u'Password:'),
        min_length=PASSWD_MIN_LENGTH,
        widget=forms.PasswordInput(render_value=False),
        error_messages={'required': PASSWD_REQUIRED,
                        'min_length': PASSWD_MIN_LENGTH_MSG})

    interested = forms.BooleanField(required=False)

    class Meta(object):
        model = User
        fields = ('email', 'username', 'password',)

    def clean(self):
        super(RegisterForm, self).clean()
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        _check_password(password)
        _check_username(username)

        return self.cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with that email address '
                                          'already exists.'))
        return email

    def __init__(self, request=None, *args, **kwargs):
        super(RegisterForm, self).__init__(request, auto_id='id_for_%s',
                                           *args, **kwargs)


class AuthenticationForm(auth_forms.AuthenticationForm):
    """Overrides the default django form.

    * Doesn't prefill password on validation error.
    * Allows logging in inactive users (initialize with `only_active=False`).
    """
    username = forms.CharField(
        label=_lazy(u'Username:'),
        error_messages={'required': USERNAME_REQUIRED})
    password = forms.CharField(
        label=_lazy(u'Password:'),
        widget=forms.PasswordInput(render_value=False),
        error_messages={'required': PASSWD_REQUIRED})

    def __init__(self, request=None, only_active=True, *args, **kwargs):
        self.only_active = only_active
        super(AuthenticationForm, self).__init__(request, *args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    _('Please enter a correct username and password. Note '
                      'that both fields are case-sensitive.'))
            elif self.only_active and not self.user_cache.is_active:
                raise forms.ValidationError(_('This account is inactive.'))

        if self.request:
            if not self.request.session.test_cookie_worked():
                raise forms.ValidationError(
                    _("Your Web browser doesn't appear to have cookies "
                      "enabled. Cookies are required for logging in."))

        return self.cleaned_data


class ProfileForm(forms.ModelForm):
    """The form for editing the user's profile."""

    involved_from = forms.DateField(
        required=False,
        label=_lazy(u'Involved with Mozilla from'),
        widget=MonthYearWidget(years=range(1998, datetime.today().year + 1),
                               required=False))

    class Meta(object):
        model = Profile
        fields = ('name', 'public_email', 'bio', 'website', 'twitter',
                  'facebook', 'mozillians', 'irc_handle', 'timezone', 'country', 'city',
                  'locale', 'involved_from')
        widgets = {
            'facebook': FacebookURLWidget,
        }

    def clean_facebook(self):
        facebook = self.cleaned_data['facebook']
        if facebook and not re.match(FacebookURLWidget.pattern, facebook):
            raise forms.ValidationError(_(u'Please enter a facebook.com URL.'))
        return facebook


class AvatarForm(forms.ModelForm):
    """The form for editing the user's avatar."""
    avatar = forms.ImageField(required=True, widget=ImageWidget)

    def __init__(self, *args, **kwargs):
        super(AvatarForm, self).__init__(*args, **kwargs)
        self.fields['avatar'].help_text = (
            _('Your avatar will be resized to {size}x{size}').format(
                size=settings.AVATAR_SIZE))

    class Meta(object):
        model = Profile
        fields = ('avatar',)

    def clean_avatar(self):
        if not ('avatar' in self.cleaned_data and self.cleaned_data['avatar']):
            return self.cleaned_data['avatar']
        try:
            check_file_size(self.cleaned_data['avatar'],
                            settings.MAX_AVATAR_FILE_SIZE)
        except FileTooLargeError as e:
            raise forms.ValidationError(e.args[0])
        clean_image_extension(self.cleaned_data.get('avatar'))
        return self.cleaned_data['avatar']


class EmailConfirmationForm(forms.Form):
    """A simple form that requires an email address."""
    email = forms.EmailField(label=_lazy(u'Email address:'))


class EmailChangeForm(forms.Form):
    """A simple form that requires an email address and validates that it is
    not the current user's email."""
    email = forms.EmailField(label=_lazy(u'Email address:'))

    def __init__(self, user, *args, **kwargs):
        super(EmailChangeForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.user.email == email:
            raise forms.ValidationError(_('This is your current email.'))
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with that email address '
                                          'already exists.'))
        return self.cleaned_data['email']


class SetPasswordForm(auth_forms.SetPasswordForm):
    new_password1 = forms.CharField(
        label=_lazy(u'New password:'),
        min_length=PASSWD_MIN_LENGTH,
        widget=forms.PasswordInput(render_value=False),
        error_messages={'required': PASSWD_REQUIRED,
                        'min_length': PASSWD_MIN_LENGTH_MSG})

    def clean(self):
        super(SetPasswordForm, self).clean()
        _check_password(self.cleaned_data.get('new_password1'))
        return self.cleaned_data


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    new_password1 = forms.CharField(
        label=_lazy(u'New password:'),
        min_length=PASSWD_MIN_LENGTH,
        widget=forms.PasswordInput(render_value=False),
        error_messages={'required': PASSWD_REQUIRED,
                        'min_length': PASSWD_MIN_LENGTH_MSG})

    def clean(self):
        super(PasswordChangeForm, self).clean()
        _check_password(self.cleaned_data.get('new_password1'))
        return self.cleaned_data


class ForgotUsernameForm(forms.Form):
    """A simple form to retrieve username.

    Requires an email address."""
    email = forms.EmailField(label=_lazy(u'Email address:'))

    def clean_email(self):
        """
        Validates that an active user exists with the given e-mail address.
        """
        email = self.cleaned_data["email"]
        try:
            self.user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            raise forms.ValidationError(
                _(u"That e-mail address doesn't have an associated user "
                  u"account. Are you sure you've registered?"))
        return email

    def save(self, text_template='users/email/forgot_username.ltxt',
             html_template='users/email/forgot_username.html', use_https=False,
             request=None):
        """Sends email with username."""
        user = self.user
        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain

        @email_utils.safe_translation
        def _send_mail(locale, user, context):
            subject = _('Your username on %s') % site_name

            mail = email_utils.make_mail(
                subject=subject,
                text_template=text_template,
                html_template=html_template,
                context_vars=context,
                from_email=settings.TIDINGS_FROM_ADDRESS,
                to_email=user.email)

            email_utils.send_messages([mail])

        c = {
            'email': user.email,
            'domain': domain,
            'login_url': reverse('users.login'),
            'site_name': site_name,
            'username': user.username,
            'protocol': use_https and 'https' or 'http'}

        # The user is not logged in, the user object comes from the
        # supplied email address, and is filled in by `clean_email`. If
        # an invalid email address was given, an exception would have
        # been raised already.
        locale = user.profile.locale or settings.WIKI_DEFAULT_LANGUAGE
        _send_mail(locale, user, c)


class PasswordResetForm(DjangoPasswordResetForm):
    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             text_template=None,
             html_template=None,
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        Based off of django's but handles html and plain-text emails.
        """
        users = User.objects.filter(
            email__iexact=self.cleaned_data["email"], is_active=True)
        for user in users:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override

            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }

            subject = email_utils.render_email(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())

            @email_utils.safe_translation
            def _make_mail(locale):
                mail = email_utils.make_mail(
                    subject=subject,
                    text_template=text_template,
                    html_template=html_template,
                    context_vars=c,
                    from_email=from_email,
                    to_email=user.email)

                return mail

            if request:
                locale = request.LANGUAGE_CODE
            else:
                locale = settings.WIKI_DEFAULT_LANGUAGE

            email_utils.send_messages([_make_mail(locale)])


def _check_password(password):
    if password:  # Oddly, empty password validation happens after this.
        if not password_re.search(password):
            msg = _('At least one number and one English letter are required '
                    'in the password.')
            raise forms.ValidationError(msg)


USERNAME_CACHE_KEY = 'username-blacklist'


def username_allowed(username):
    if not username:
        return False
    """Returns True if the given username is not a blatent bad word."""
    blacklist = cache.get(USERNAME_CACHE_KEY)
    if blacklist is None:
        f = open(settings.USERNAME_BLACKLIST, 'r')
        blacklist = [w.strip() for w in f.readlines()]
        cache.set(USERNAME_CACHE_KEY, blacklist, 60 * 60)  # 1 hour
    # Lowercase
    username = username.lower()
    # Add lowercased and non alphanumerics to start.
    usernames = set([username, re.sub("\W", "", username)])
    # Add words split on non alphanumerics.
    for u in re.findall(r'\w+', username):
        usernames.add(u)
    # Do any match the bad words?
    return not usernames.intersection(blacklist)


def _check_username(username):
    if username and not username_allowed(username):
        msg = _('The user name you entered is inappropriate. Please pick '
                'another and consider that our helpers are other Firefox '
                'users just like you.')
        raise forms.ValidationError(msg)
