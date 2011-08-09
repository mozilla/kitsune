import datetime
import hashlib
import random
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.db import models
from django.template.loader import render_to_string

from statsd import statsd
from timezones.fields import TimeZoneField
from tower import ugettext as _
from tower import ugettext_lazy as _lazy

from countries import COUNTRIES
from sumo.models import ModelBase, LocaleField
from sumo.urlresolvers import reverse
from sumo.utils import auto_delete_files


SHA1_RE = re.compile('^[a-f0-9]{40}$')


@auto_delete_files
class Profile(ModelBase):
    """Profile model for django users, get it with user.get_profile()."""

    user = models.OneToOneField(User, primary_key=True,
                                verbose_name=_lazy(u'User'))
    name = models.CharField(max_length=255, null=True, blank=True,
                            verbose_name=_lazy(u'Display name'))
    public_email = models.BooleanField(  # show/hide email
        default=False, verbose_name=_lazy(u'Make my email public'))
    avatar = models.ImageField(upload_to=settings.USER_AVATAR_PATH, null=True,
                               blank=True, verbose_name=_lazy(u'Avatar'),
                               max_length=settings.MAX_FILEPATH_LENGTH)
    bio = models.TextField(null=True, blank=True,
                           verbose_name=_lazy(u'Biography'))
    website = models.URLField(max_length=255, null=True, blank=True,
                              verify_exists=False,
                              verbose_name=_lazy(u'Website'))
    twitter = models.URLField(max_length=255, null=True, blank=True,
                              verify_exists=False,
                              verbose_name=_lazy(u'Twitter URL'))
    facebook = models.URLField(max_length=255, null=True, blank=True,
                               verify_exists=False,
                               verbose_name=_lazy(u'Facebook URL'))
    irc_handle = models.CharField(max_length=255, null=True, blank=True,
                                  verbose_name=_lazy(u'IRC nickname'))
    timezone = TimeZoneField(null=True, blank=True,
                             verbose_name=_lazy(u'Timezone'))
    country = models.CharField(max_length=2, choices=COUNTRIES, null=True,
                               blank=True, verbose_name=_lazy(u'Country'))
    # No city validation
    city = models.CharField(max_length=255, null=True, blank=True,
                            verbose_name=_lazy(u'City'))
    livechat_id = models.CharField(default=None, null=True, blank=True,
                                   max_length=255,
                                   verbose_name=_lazy(u'Livechat ID'))
    locale = LocaleField(default=settings.LANGUAGE_CODE,
                         verbose_name=_lazy(u'Preferred language for email'))

    class Meta(object):
        permissions = (('view_karma_points', 'Can view karma points'),)

    def __unicode__(self):
        return unicode(self.user)

    def get_absolute_url(self):
        return reverse('users.profile', args=[self.user_id])


# Activation model and manager:
# (based on http://bitbucket.org/ubernostrum/django-registration)
class ConfirmationManager(models.Manager):
    """
    Custom manager for confirming keys sent by email.

    The methods defined here provide shortcuts for creation of instances
    and sending email confirmations.
    Activation should be done in specific managers.
    """
    def _send_email(self, confirmation_profile, url,
                    subject, email_template, send_to, **kwargs):
        """
        Send an email using a passed in confirmation profile.

        Use specified url, subject, email_template, and email to send_to.
        """
        current_site = Site.objects.get_current()
        email_kwargs = {'activation_key': confirmation_profile.activation_key,
                        'domain': current_site.domain,
                        'activate_url': url}
        email_kwargs.update(kwargs)
        message = render_to_string(email_template, email_kwargs)
        mail.send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                       [send_to])

    def send_confirmation_email(self, *args, **kwargs):
        """This is meant to be overwritten."""
        raise NotImplementedError

    def create_profile(self, user, *args, **kwargs):
        """
        Create an instance of this manager's object class for a given
        ``User``, and return it.

        The activation key will be a SHA1 hash, generated from a combination
        of the ``User``'s username and a random salt.
        """
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        activation_key = hashlib.sha1(salt + user.username).hexdigest()
        return self.create(user=user, activation_key=activation_key, **kwargs)


class RegistrationManager(ConfirmationManager):
    def get_user(self, activation_key):
        """Get the user for the specified activation_key."""
        try:
            profile = self.get(activation_key=activation_key)
            return profile.user
        except self.model.DoesNotExist:
            return None

    def activate_user(self, activation_key, request=None):
        """
        Validate an activation key and activate the corresponding
        ``User`` if valid.

        If the key is valid and has not expired, return the ``User``
        after activating.

        If the key is not valid or has expired, return ``False``.
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search(activation_key):
            try:
                profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                profile = None
                statsd.incr('user.activate-error.does-not-exist')
                msg = 'Key: {k}\nRequest:\n'.format(k=activation_key)
                reason = 'key not found'
            if profile:
                if not profile.activation_key_expired():
                    user = profile.user
                    user.is_active = True
                    user.save()
                    return user
                else:
                    statsd.incr('user.activate-error.expired')
                    msg = 'Username: {u}\nJoined: {d}\nRequest:\n'
                    msg = msg.format(u=profile.user.username,
                                     d=profile.user.date_joined)
                    reason = 'key expired'
        else:
            statsd.incr('user.activate-error.invalid-key')
            msg = 'Key: {k}\nRequest:\n'.format(k=activation_key)
            reason = 'invalid key'

        mail.mail_admins(u'User activation failure ({r})'.format(r=reason),
                         msg + repr(request), fail_silently=True)

        return False

    def create_inactive_user(self, username, password, email,
                             locale=settings.LANGUAGE_CODE,
                             email_template=None, email_subject=None,
                             email_data=None):
        """
        Create a new, inactive ``User`` and ``Profile``, generates a
        ``RegistrationProfile`` and email its activation key to the
        ``User``, returning the new ``User``.
        """
        new_user = User.objects.create_user(username, email, password)
        new_user.is_active = False
        new_user.save()
        Profile.objects.create(user=new_user, locale=locale)

        registration_profile = self.create_profile(new_user)

        self.send_confirmation_email(registration_profile, email_template,
                                     email_subject, email_data)

        return new_user

    def send_confirmation_email(self, registration_profile,
                                email_template=None, email_subject=None,
                                email_data=None):
        """Send the user confirmation email."""
        user_id = registration_profile.user.id
        key = registration_profile.activation_key
        self._send_email(
            confirmation_profile=registration_profile,
            url=reverse('users.activate', args=[user_id, key]),
            subject=email_subject or _('Please confirm your email address'),
            email_template=email_template or 'users/email/activate.ltxt',
            send_to=registration_profile.user.email,
            expiration_days=settings.ACCOUNT_ACTIVATION_DAYS,
            username=registration_profile.user.username,
            email_data=email_data)

    def delete_expired_users(self):
        """
        Remove expired instances of this manager's object class.

        Accounts to be deleted are identified by searching for
        instances of this manager's object class with expired activation
        keys, and then checking to see if their associated ``User``
        instances have the field ``is_active`` set to ``False``; any
        ``User`` who is both inactive and has an expired activation
        key will be deleted.
        """
        for profile in self.all():
            if profile.activation_key_expired():
                profile.delete()
                # TODO: We need to limit non-active users actions to just
                # asking a question (no posting to forums, etc.). Then
                # we can safely delete them here to free up the usernames.
                #user = profile.user
                #if not user.is_active:
                #    user.delete()


class EmailChangeManager(ConfirmationManager):
    def send_confirmation_email(self, email_change, new_email):
        """Ask for confirmation before changing a user's email."""
        self._send_email(
            confirmation_profile=email_change,
            url=reverse('users.confirm_email',
                        args=[email_change.activation_key]),
            subject=_('Please confirm your email address'),
            email_template='users/email/confirm_email.ltxt',
            send_to=new_email)


class RegistrationProfile(models.Model):
    """
    A simple profile which stores an activation key used for
    user account registration.

    Generally, you will not want to interact directly with instances
    of this model; the provided manager includes methods
    for creating and activating new accounts.
    """
    user = models.ForeignKey(User, unique=True, verbose_name=_lazy(u'user'))
    activation_key = models.CharField(verbose_name=_lazy(u'activation key'),
                                      max_length=40)

    objects = RegistrationManager()

    class Meta:
        verbose_name = _lazy(u'registration profile')
        verbose_name_plural = _lazy(u'registration profiles')

    def __unicode__(self):
        return u'Registration information for %s' % self.user

    def activation_key_expired(self):
        """
        Determine whether this ``RegistrationProfile``'s activation
        key has expired, returning a boolean -- ``True`` if the key
        has expired.

        Key expiration is determined by:
        1. The date the user signed up is incremented by
           the number of days specified in the setting
           ``ACCOUNT_ACTIVATION_DAYS`` (which should be the number of
           days after signup during which a user is allowed to
           activate their account); if the result is less than or
           equal to the current date, the key has expired and this
           method returns ``True``.
        """
        exp_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.user.date_joined + exp_date <= datetime.datetime.now()
    activation_key_expired.boolean = True


class EmailChange(models.Model):
    """Stores email with activation key when user requests a change."""
    ACTIVATED = u"ALREADY_ACTIVATED"

    user = models.ForeignKey(User, unique=True, verbose_name=_lazy(u'user'))
    activation_key = models.CharField(verbose_name=_lazy(u'activation key'),
                                      max_length=40)
    email = models.EmailField(db_index=True, null=True)

    objects = EmailChangeManager()

    def __unicode__(self):
        return u'Change email request to %s for %s' % (self.email, self.user)
