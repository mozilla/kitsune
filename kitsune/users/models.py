import hashlib
import logging
import random
import re
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy as _lazy

from celery.task import task
from statsd import statsd
from timezones.fields import TimeZoneField

from kitsune.lib.countries import COUNTRIES
from kitsune.search.es_utils import UnindexMeBro
from kitsune.search.models import (
    SearchMappingType, SearchMixin, register_for_indexing,
    register_mapping_type)
from kitsune.sumo import email_utils
from kitsune.sumo.models import ModelBase, LocaleField
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import auto_delete_files, chunked
from kitsune.users.validators import TwitterValidator


log = logging.getLogger('k.users')


SHA1_RE = re.compile('^[a-f0-9]{40}$')
CONTRIBUTOR_GROUP = 'Registered as contributor'


@auto_delete_files
class Profile(ModelBase, SearchMixin):
    """Profile model for django users."""

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
                              verbose_name=_lazy(u'Website'))
    twitter = models.CharField(max_length=15, null=True, blank=True, validators=[TwitterValidator],
                               verbose_name=_lazy(u'Twitter Username'))
    facebook = models.URLField(max_length=255, null=True, blank=True,
                               verbose_name=_lazy(u'Facebook URL'))
    mozillians = models.CharField(max_length=255, null=True, blank=True,
                                  verbose_name=_lazy(u'Mozillians Username'))
    irc_handle = models.CharField(max_length=255, null=True, blank=True,
                                  verbose_name=_lazy(u'IRC nickname'))
    timezone = TimeZoneField(null=True, blank=True,
                             verbose_name=_lazy(u'Timezone'))
    country = models.CharField(max_length=2, choices=COUNTRIES, null=True,
                               blank=True, verbose_name=_lazy(u'Country'))
    # No city validation
    city = models.CharField(max_length=255, null=True, blank=True,
                            verbose_name=_lazy(u'City'))
    locale = LocaleField(default=settings.LANGUAGE_CODE,
                         verbose_name=_lazy(u'Preferred language'))
    first_answer_email_sent = models.BooleanField(
        default=False, help_text=_lazy(u'Has been sent a first answer contribution email.'))
    first_l10n_email_sent = models.BooleanField(
        default=False, help_text=_lazy(u'Has been sent a first revision contribution email.'))
    involved_from = models.DateField(null=True, blank=True,
                                     verbose_name=_lazy(u'Involved with Mozilla from'))
    csat_email_sent = models.DateField(null=True, blank=True,
                                       verbose_name=_lazy(u'When the user was sent a community '
                                                          u'health survey'))

    class Meta(object):
        permissions = (('view_karma_points', 'Can view karma points'),
                       ('deactivate_users', 'Can deactivate users'),
                       ('screen_share', 'Can screen share'),)

    def __unicode__(self):
        try:
            return unicode(self.user)
        except Exception as exc:
            return unicode('%d (%r)' % (self.pk, exc))

    def get_absolute_url(self):
        return reverse('users.profile', args=[self.user_id])

    def clear(self):
        """Clears out the users profile"""
        self.name = ''
        self.public_email = False
        self.avatar = None
        self.bio = ''
        self.website = ''
        self.twitter = ''
        self.facebook = ''
        self.mozillians = ''
        self.irc_handle = ''
        self.city = ''

    @property
    def display_name(self):
        return self.name if self.name else self.user.username

    @property
    def twitter_usernames(self):
        from kitsune.customercare.models import Reply
        return list(
            Reply.objects.filter(user=self.user)
                         .values_list('twitter_username', flat=True)
                         .distinct())

    @classmethod
    def get_mapping_type(cls):
        return UserMappingType

    @classmethod
    def get_serializer(cls, serializer_type='full'):
        # Avoid circular import
        from kitsune.users import api
        if serializer_type == 'full':
            return api.ProfileSerializer
        elif serializer_type == 'fk':
            return api.ProfileFKSerializer
        else:
            raise ValueError('Unknown serializer type "{}".'.format(serializer_type))

    @property
    def last_contribution_date(self):
        """Get the date of the user's last contribution."""
        from kitsune.customercare.models import Reply
        from kitsune.questions.models import Answer
        from kitsune.wiki.models import Revision

        dates = []

        # Latest Army of Awesome reply:
        try:
            aoa_reply = Reply.objects.filter(
                user=self.user).latest('created')
            dates.append(aoa_reply.created)
        except Reply.DoesNotExist:
            pass

        # Latest Support Forum answer:
        try:
            answer = Answer.objects.filter(
                creator=self.user).latest('created')
            dates.append(answer.created)
        except Answer.DoesNotExist:
            pass

        # Latest KB Revision edited:
        try:
            revision = Revision.objects.filter(
                creator=self.user).latest('created')
            dates.append(revision.created)
        except Revision.DoesNotExist:
            pass

        # Latest KB Revision reviewed:
        try:
            revision = Revision.objects.filter(
                reviewer=self.user).latest('reviewed')
            # Old revisions don't have the reviewed date.
            dates.append(revision.reviewed or revision.created)
        except Revision.DoesNotExist:
            pass

        if len(dates) == 0:
            return None

        return max(dates)

    @property
    def settings(self):
        return self.user.settings

    @property
    def answer_helpfulness(self):
        # Avoid circular import
        from kitsune.questions.models import AnswerVote
        return AnswerVote.objects.filter(answer__creator=self.user, helpful=True).count()


@register_mapping_type
class UserMappingType(SearchMappingType):
    list_keys = [
        'twitter_usernames',
        'itwitter_usernames',
    ]

    @classmethod
    def get_model(cls):
        return Profile

    @classmethod
    def get_index_group(cls):
        return 'non-critical'

    @classmethod
    def get_mapping(cls):
        return {
            'properties': {
                'id': {'type': 'long'},
                'model': {'type': 'string', 'index': 'not_analyzed'},
                'url': {'type': 'string', 'index': 'not_analyzed'},
                'indexed_on': {'type': 'integer'},

                'username': {'type': 'string', 'index': 'not_analyzed'},
                'display_name': {'type': 'string', 'index': 'not_analyzed'},
                'twitter_usernames': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },

                'last_contribution_date': {'type': 'date'},

                # lower-cased versions for querying:
                'iusername': {'type': 'string', 'index': 'not_analyzed'},
                'idisplay_name': {'type': 'string', 'analyzer': 'whitespace'},
                'itwitter_usernames': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },

                'avatar': {'type': 'string', 'index': 'not_analyzed'},

                'suggest': {
                    'type': 'completion',
                    'index_analyzer': 'whitespace',
                    'search_analyzer': 'whitespace',
                    'payloads': True,
                }
            }
        }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        """Extracts interesting thing from a Thread and its Posts"""
        if obj is None:
            model = cls.get_model()
            obj = model.objects.select_related('user').get(pk=obj_id)

        if not obj.user.is_active:
            raise UnindexMeBro()

        d = {}
        d['id'] = obj.pk
        d['model'] = cls.get_mapping_type_name()
        d['url'] = obj.get_absolute_url()
        d['indexed_on'] = int(time.time())

        d['username'] = obj.user.username
        d['display_name'] = obj.display_name
        d['twitter_usernames'] = obj.twitter_usernames

        d['last_contribution_date'] = obj.last_contribution_date

        d['iusername'] = obj.user.username.lower()
        d['idisplay_name'] = obj.display_name.lower()
        d['itwitter_usernames'] = [u.lower() for u in obj.twitter_usernames]

        from kitsune.users.templatetags.jinja_helpers import profile_avatar
        d['avatar'] = profile_avatar(obj.user, size=120)

        d['suggest'] = {
            'input': [
                d['iusername'],
                d['idisplay_name']
            ],
            'output': _(u'{displayname} ({username})').format(
                displayname=d['display_name'], username=d['username']),
            'payload': {'user_id': d['id']},
        }

        return d

    @classmethod
    def suggest_completions(cls, text):
        """Suggest completions for the text provided."""
        USER_SUGGEST = 'user-suggest'
        es = UserMappingType.search().get_es()

        results = es.suggest(index=cls.get_index(), body={
            USER_SUGGEST: {
                'text': text.lower(),
                'completion': {
                    'field': 'suggest'
                }
            }
        })

        if results[USER_SUGGEST][0]['length'] > 0:
            return results[USER_SUGGEST][0]['options']

        return []


register_for_indexing('users', Profile)


def get_profile(u):
    try:
        return Profile.objects.get(user=u)
    except Profile.DoesNotExist:
        return None


register_for_indexing(
    'users',
    User,
    instance_to_indexee=get_profile)


class Setting(ModelBase):
    """User specific value per setting"""
    user = models.ForeignKey(User, verbose_name=_lazy(u'User'),
                             related_name='settings')

    name = models.CharField(max_length=100)
    value = models.CharField(blank=True, max_length=60,
                             verbose_name=_lazy(u'Value'))

    class Meta(object):
        unique_together = (('user', 'name'),)

    def __unicode__(self):
        return u'%s %s:%s' % (self.user, self.name, self.value or u'[none]')

    @classmethod
    def get_for_user(cls, user, name):
        from kitsune.users.forms import SettingsForm
        form = SettingsForm()
        if name not in form.fields.keys():
            raise KeyError(("'{name}' is not a field in "
                            "user.forms.SettingsFrom()").format(name=name))
        try:
            setting = Setting.objects.get(user=user, name=name)
        except Setting.DoesNotExist:
            value = form.fields[name].initial or ''
            setting = Setting.objects.create(user=user, name=name, value=value)
        # Cast to the field's Python type.
        return form.fields[name].to_python(setting.value)


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
                    subject, text_template, html_template,
                    send_to, **kwargs):
        """
        Send an email using a passed in confirmation profile.

        Use specified url, subject, text_template, html_template and
        email to send_to.
        """
        current_site = Site.objects.get_current()
        email_kwargs = {'activation_key': confirmation_profile.activation_key,
                        'domain': current_site.domain,
                        'activate_url': url,
                        'login_url': reverse('users.login'),
                        'reg': 'main'}
        email_kwargs.update(kwargs)

        # RegistrationProfile doesn't have a locale attribute. So if
        # we get one of those, then we have to get the real profile
        # from the user.
        if hasattr(confirmation_profile, 'locale'):
            locale = confirmation_profile.locale
        else:
            locale = confirmation_profile.user.profile.locale

        @email_utils.safe_translation
        def _make_mail(locale):
            mail = email_utils.make_mail(
                subject=subject,
                text_template=text_template,
                html_template=html_template,
                context_vars=email_kwargs,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=send_to)

            return mail

        email_utils.send_messages([_make_mail(locale)])

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
                reason = 'key not found'
            if profile:
                if not profile.activation_key_expired():
                    user = profile.user
                    user.is_active = True
                    user.save()

                    # We don't need the RegistrationProfile anymore, delete it.
                    profile.delete()

                    # If user registered as contributor, send them the
                    # welcome email.
                    if user.groups.filter(name=CONTRIBUTOR_GROUP):
                        self._send_email(
                            confirmation_profile=profile,
                            url=None,
                            subject=_('Welcome to SUMO!'),
                            text_template='users/email/contributor.ltxt',
                            html_template='users/email/contributor.html',
                            send_to=user.email,
                            contributor=user)

                    return user
                else:
                    statsd.incr('user.activate-error.expired')
                    reason = 'key expired'
        else:
            statsd.incr('user.activate-error.invalid-key')
            reason = 'invalid key'

        log.warning(u'User activation failure ({r}): {k}'.format(
            r=reason, k=activation_key))

        return False

    def create_inactive_user(self, username, password, email,
                             locale=settings.LANGUAGE_CODE,
                             text_template=None, html_template=None,
                             subject=None, email_data=None,
                             volunteer_interest=False, **kwargs):
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

        self.send_confirmation_email(
            registration_profile,
            text_template,
            html_template,
            subject,
            email_data,
            **kwargs)

        if volunteer_interest:
            statsd.incr('user.registered-as-contributor')
            group = Group.objects.get(name=CONTRIBUTOR_GROUP)
            new_user.groups.add(group)

        return new_user

    def send_confirmation_email(self, registration_profile,
                                text_template=None, html_template=None,
                                subject=None, email_data=None, **kwargs):
        """Send the user confirmation email."""
        user_id = registration_profile.user.id
        key = registration_profile.activation_key
        self._send_email(
            confirmation_profile=registration_profile,
            url=reverse('users.activate', args=[user_id, key]),
            subject=subject or _('Please confirm your email address'),
            text_template=text_template or 'users/email/activate.ltxt',
            html_template=html_template or 'users/email/activate.html',
            send_to=registration_profile.user.email,
            expiration_days=settings.ACCOUNT_ACTIVATION_DAYS,
            username=registration_profile.user.username,
            email_data=email_data,
            **kwargs)

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
        days_valid = settings.ACCOUNT_ACTIVATION_DAYS
        expired = datetime.now() - timedelta(days=days_valid)
        prof_ids = self.filter(user__date_joined__lt=expired)
        prof_ids = prof_ids.values_list('id', flat=True)
        for chunk in chunked(prof_ids, 1000):
            _delete_registration_profiles_chunk.apply_async(args=[chunk])


@task
def _delete_registration_profiles_chunk(data):
    log_msg = u'Deleting {num} expired registration profiles.'
    log.info(log_msg.format(num=len(data)))
    qs = RegistrationProfile.objects.filter(id__in=data)
    for profile in qs.select_related('user'):
        user = profile.user
        profile.delete()
        if user and not user.is_active:
            user.delete()


class EmailChangeManager(ConfirmationManager):
    def send_confirmation_email(self, email_change, new_email):
        """Ask for confirmation before changing a user's email."""
        self._send_email(
            confirmation_profile=email_change,
            url=reverse('users.confirm_email',
                        args=[email_change.activation_key]),
            subject=_('Please confirm your email address'),
            text_template='users/email/confirm_email.ltxt',
            html_template='users/email/confirm_email.html',
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
        exp_date = timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.user.date_joined + exp_date <= datetime.now()
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


class Deactivation(models.Model):
    """Stores user deactivation logs."""
    user = models.ForeignKey(User, verbose_name=_lazy(u'user'),
                             related_name='+')
    moderator = models.ForeignKey(User, verbose_name=_lazy(u'moderator'),
                                  related_name='deactivations')
    date = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return u'%s was deactivated by %s on %s' % (self.user, self.moderator,
                                                    self.date)
