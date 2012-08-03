import re

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, forms as auth_forms
from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site
from django.core.mail import send_mail
from django.template import Context, loader

from tower import ugettext as _, ugettext_lazy as _lazy

from sumo.urlresolvers import reverse
from sumo.widgets import ImageWidget
from upload.forms import clean_image_extension
from upload.utils import check_file_size, FileTooLargeError
from users.models import Profile
from users.passwords import password_allowed, username_allowed
from users.widgets import FacebookURLWidget, TwitterURLWidget


USERNAME_INVALID = _lazy(u'Username may contain only letters, '
                         'numbers and ./+/-/_ characters.')
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
        regex=r'^[\w.+-]+$',
        help_text=_lazy(u'Required. 30 characters or fewer. Letters, digits '
                         'and ./+/-/_ only.'),
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
    password2 = forms.CharField(
        label=_lazy(u'Repeat password:'),
        widget=forms.PasswordInput(render_value=False),
        error_messages={'required': PASSWD2_REQUIRED},
        help_text=_lazy(u'Enter the same password as '
                         'above, for verification.'))

    interested = forms.BooleanField(
        label=_lazy(u'I am interested in volunteering to help other '
                     'Mozilla users'),
        required=False)

    class Meta(object):
        model = User
        fields = ('username', 'password', 'password2', 'email')

    def clean(self):
        super(RegisterForm, self).clean()
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if not password == password2:
            raise forms.ValidationError(_('Passwords must match.'))

        _check_password(password)
        _check_username(username)

        return self.cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with that email address '
                                          'already exists.'))
        return email

    def __init__(self,  request=None, *args, **kwargs):
        super(RegisterForm, self).__init__(request, auto_id='id_for_%s',
                                           *args, **kwargs)


class AuthenticationForm(auth_forms.AuthenticationForm):
    """Overrides the default django form.

    * Doesn't prefill password on validation error.
    * Allows logging in inactive users (initialize with `only_active=False`).
    """
    password = forms.CharField(label=_lazy(u"Password"),
                               widget=forms.PasswordInput(render_value=False))

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

    class Meta(object):
        model = Profile
        fields = ('name', 'public_email', 'bio', 'website', 'twitter',
                  'facebook', 'irc_handle', 'timezone', 'country', 'city',
                  'locale')
        widgets = {
            'twitter': TwitterURLWidget,
            'facebook': FacebookURLWidget,
        }

    def clean_twitter(self):
        twitter = self.cleaned_data['twitter']
        if twitter and not re.match(TwitterURLWidget.pattern, twitter):
            raise forms.ValidationError(_(u'Please enter a twitter.com URL.'))
        return twitter

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
            u'Your avatar will be resized to {size}x{size}'.format(
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
                _(u"That e-mail address doesn't have an associated user"
                   " account. Are you sure you've registered?"))
        return email

    def save(self, email_template='users/email/forgot_username.ltxt',
             use_https=False, request=None):
        """Sends email with username."""
        user = self.user
        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain
        t = loader.get_template(email_template)
        c = {
            'email': user.email,
            'domain': domain,
            'login_url': reverse('users.login'),
            'site_name': site_name,
            'username': user.username,
            'protocol': use_https and 'https' or 'http'}
        send_mail(
            _("Your username on %s") % site_name,
            t.render(Context(c)), settings.TIDINGS_FROM_ADDRESS, [user.email])


def _check_password(password):
    if password:  # Oddly, empty password validation happens after this.
        if not password_allowed(password):
            msg = _('The password entered is known to be commonly used and '
                    'is not allowed.')
            raise forms.ValidationError(msg)

        if not password_re.search(password):
            msg = _('At least one number and one English letter are required '
                    'in the password.')
            raise forms.ValidationError(msg)


def _check_username(username):
    if not username_allowed(username):
        msg = _('The user name you entered is inappropriate. Please pick '
                'another and consider that our helpers are other Firefox '
                'users just like you.')
        raise forms.ValidationError(msg)
