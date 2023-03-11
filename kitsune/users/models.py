import logging
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.cache import caches
from django.core.mail import send_mail
from django.db import models
from django.db.models.manager import EmptyManager
from django.utils.itercompat import is_iterable
from django.utils.translation import gettext_lazy as _lazy
from timezone_field import TimeZoneField

from kitsune.lib.countries import COUNTRIES
from kitsune.products.models import Product
from kitsune.sumo.models import LocaleField, ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import auto_delete_files
from kitsune.users.validators import TwitterValidator

log = logging.getLogger("k.users")


SHA1_RE = re.compile("^[a-f0-9]{40}$")
SET_ID_PREFIX = "https://schemas.accounts.firefox.com/event/"


class ContributionAreas(models.TextChoices):
    KB = "kb-contributors", _lazy("KB Contributors")
    L10N = "l10n-contributors", _lazy("L10n Contributors")
    FORUM = "forum-contributors", _lazy("Forum Contributors")
    SOCIAL = "social-contributors", _lazy("Social media Contributors")
    MOBILE = "mobile-contributors", _lazy("Mobile support Contributors")

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_values(cls):
        return [item.value for item in cls]

    @classmethod
    def get_groups(cls):
        """Transitional class method that will return both old and new groups."""
        return cls.get_values() + settings.LEGACY_CONTRIBUTOR_GROUPS

    @classmethod
    def has_member(cls, value):
        return value in cls._member_names_


@auto_delete_files
class Profile(ModelBase):
    """Profile model for django users."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, verbose_name=_lazy("User")
    )
    name = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_lazy("Display name")
    )
    public_email = models.BooleanField(  # show/hide email
        default=False, verbose_name=_lazy("Make my email address visible to logged in users")
    )
    avatar = models.ImageField(
        upload_to=settings.USER_AVATAR_PATH,
        null=True,
        blank=True,
        verbose_name=_lazy("Avatar"),
        max_length=settings.MAX_FILEPATH_LENGTH,
    )
    bio = models.TextField(
        null=True,
        blank=True,
        verbose_name=_lazy("Biography"),
        help_text=_lazy(
            "Some HTML supported: &#x3C;abbr title&#x3E; "
            + "&#x3C;acronym title&#x3E; &#x3C;b&#x3E; "
            + "&#x3C;blockquote&#x3E; &#x3C;code&#x3E; "
            + "&#x3C;em&#x3E; &#x3C;i&#x3E; &#x3C;li&#x3E; "
            + "&#x3C;ol&#x3E; &#x3C;strong&#x3E; &#x3C;ul&#x3E;. "
            + "Links are forbidden."
        ),
    )
    website = models.URLField(max_length=255, null=True, blank=True, verbose_name=_lazy("Website"))
    twitter = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        validators=[TwitterValidator],
        verbose_name=_lazy("Twitter Username"),
    )
    community_mozilla_org = models.CharField(
        max_length=255, default="", blank=True, verbose_name=_lazy("Community Portal Username")
    )
    people_mozilla_org = models.CharField(
        max_length=255, blank=True, default="", verbose_name=_lazy("People Directory Username")
    )
    matrix_handle = models.CharField(
        max_length=255, default="", blank=True, verbose_name=_lazy("Matrix Nickname")
    )
    timezone = TimeZoneField(
        null=True, blank=True, default="US/Pacific", verbose_name=_lazy("Timezone")
    )
    country = models.CharField(
        max_length=2, choices=COUNTRIES, null=True, blank=True, verbose_name=_lazy("Country")
    )
    # No city validation
    city = models.CharField(max_length=255, null=True, blank=True, verbose_name=_lazy("City"))
    locale = LocaleField(default=settings.LANGUAGE_CODE, verbose_name=_lazy("Preferred language"))
    first_answer_email_sent = models.BooleanField(
        default=False, help_text=_lazy("Has been sent a first answer contribution email.")
    )
    first_l10n_email_sent = models.BooleanField(
        default=False, help_text=_lazy("Has been sent a first revision contribution email.")
    )
    involved_from = models.DateField(
        null=True, blank=True, verbose_name=_lazy("Involved with Mozilla from")
    )
    csat_email_sent = models.DateField(
        null=True,
        blank=True,
        verbose_name=_lazy("When the user was sent a community " "health survey"),
    )
    is_fxa_migrated = models.BooleanField(default=False)
    fxa_uid = models.CharField(blank=True, null=True, unique=True, max_length=128)
    fxa_avatar = models.URLField(max_length=512, blank=True, default="")
    products = models.ManyToManyField(Product, related_name="subscribed_users")
    fxa_password_change = models.DateTimeField(blank=True, null=True)
    fxa_refresh_token = models.CharField(blank=True, default="", max_length=128)
    zendesk_id = models.CharField(blank=True, default="", max_length=1024)

    updated_column_name = "user__date_joined"

    class Meta(object):
        permissions = (
            ("view_karma_points", "Can view karma points"),
            ("deactivate_users", "Can deactivate users"),
        )

    def __str__(self):
        try:
            return str(self.user)
        except Exception as exc:
            return str("%d (%r)" % (self.pk, exc))

    def get_absolute_url(self):
        return reverse("users.profile", args=[self.user_id])

    def clear(self):
        """Clears out the users profile"""
        self.name = ""
        self.public_email = False
        self.avatar = None
        self.bio = ""
        self.website = ""
        self.twitter = ""
        self.community_mozilla_org = ""
        self.people_mozilla_org = ""
        self.matrix_handle = ""
        self.city = ""
        self.is_fxa_migrated = False
        self.fxa_uid = ""

    @property
    def display_name(self):
        return self.name if self.name else self.user.username

    @classmethod
    def get_serializer(cls, serializer_type="full"):
        # Avoid circular import
        from kitsune.users import api

        if serializer_type == "full":
            return api.ProfileSerializer
        elif serializer_type == "fk":
            return api.ProfileFKSerializer
        else:
            raise ValueError('Unknown serializer type "{}".'.format(serializer_type))

    @property
    def last_contribution_date(self):
        """Get the date of the user's last contribution."""
        from kitsune.questions.models import Answer
        from kitsune.wiki.models import Revision

        dates = []

        # Latest Support Forum answer:
        try:
            answer = Answer.objects.filter(creator=self.user).latest("created")
            dates.append(answer.created)
        except Answer.DoesNotExist:
            pass

        # Latest KB Revision edited:
        try:
            revision = Revision.objects.filter(creator=self.user).latest("created")
            dates.append(revision.created)
        except Revision.DoesNotExist:
            pass

        # Latest KB Revision reviewed:
        try:
            revision = Revision.objects.filter(reviewer=self.user).latest("reviewed")
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

    @property
    def is_subscriber(self):
        return self.products.exists()


class Setting(ModelBase):
    """User specific value per setting"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_lazy("User"), related_name="settings"
    )

    name = models.CharField(max_length=100)
    value = models.CharField(blank=True, max_length=60, verbose_name=_lazy("Value"))

    class Meta(object):
        unique_together = (("user", "name"),)

    def __str__(self):
        return "%s %s:%s" % (self.user, self.name, self.value or "[none]")

    @classmethod
    def get_for_user(cls, user, name):
        from kitsune.users.forms import SettingsForm

        form = SettingsForm()
        if name not in list(form.fields.keys()):
            raise KeyError(
                ("'{name}' is not a field in user.forms.SettingsFrom()").format(name=name)
            )
        try:
            setting = Setting.objects.get(user=user, name=name)
        except Setting.DoesNotExist:
            value = form.fields[name].initial or ""
            setting = Setting.objects.create(user=user, name=name, value=value)
        # Cast to the field's Python type.
        return form.fields[name].to_python(setting.value)


class RegistrationProfile(models.Model):
    """
    A simple profile which stores an activation key used for
    user account registration.

    Generally, you will not want to interact directly with instances
    of this model; the provided manager includes methods
    for creating and activating new accounts.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, unique=True, verbose_name=_lazy("user")
    )
    activation_key = models.CharField(verbose_name=_lazy("activation key"), max_length=40)

    class Meta:
        verbose_name = _lazy("registration profile")
        verbose_name_plural = _lazy("registration profiles")

    def __str__(self):
        return "Registration information for %s" % self.user

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
        return True

    activation_key_expired.boolean = True  # type: ignore


class EmailChange(models.Model):
    """Stores email with activation key when user requests a change."""

    ACTIVATED = "ALREADY_ACTIVATED"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, unique=True, verbose_name=_lazy("user")
    )
    activation_key = models.CharField(verbose_name=_lazy("activation key"), max_length=40)
    email = models.EmailField(db_index=True, null=True)

    def __str__(self):
        return "Change email request to %s for %s" % (self.email, self.user)


class Deactivation(models.Model):
    """Stores user deactivation logs."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_lazy("user"), related_name="+"
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_lazy("moderator"),
        related_name="deactivations",
    )
    date = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return "%s was deactivated by %s on %s" % (self.user, self.moderator, self.date)


class AccountEvent(models.Model):
    """Stores the events received from Firefox Accounts.

    These events are processed by celery and the correct status is assigned in each entry.
    """

    # Status of an event entry.
    UNPROCESSED = 1
    PROCESSED = 2
    IGNORED = 3
    NOT_IMPLEMENTED = 4
    EVENT_STATUS = (
        (UNPROCESSED, "unprocessed"),
        (PROCESSED, "processed"),
        (IGNORED, "ignored"),
        (NOT_IMPLEMENTED, "not-implemented"),
    )

    PASSWORD_CHANGE = "password-change"
    PROFILE_CHANGE = "profile-change"
    SUBSCRIPTION_STATE_CHANGE = "subscription-state-change"
    DELETE_USER = "delete-user"

    status = models.PositiveSmallIntegerField(
        choices=EVENT_STATUS, default=UNPROCESSED, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    body = models.TextField(max_length=4096, blank=False)
    event_type = models.CharField(max_length=256, default="", blank=True)
    fxa_uid = models.CharField(max_length=128, default="", blank=True)
    jwt_id = models.CharField(max_length=256)
    issued_at = models.CharField(max_length=32)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="account_events", null=True
    )

    class Meta(object):
        ordering = ["-last_modified"]


class UserProxyProfile:
    """A class that mimics a profile for a user proxy."""

    SESSION_ATTRIBUTES = frozenset(
        ("name", "locale", "fxa_uid", "fxa_avatar", "fxa_refresh_token", "zendesk_id")
    )

    def __init__(self, user):
        self.user = user

    def __getattr__(self, name):
        if name not in self.SESSION_ATTRIBUTES:
            raise AttributeError(name)
        return getattr(self.user, name)

    def __setattr__(self, name, value):
        if name in self.SESSION_ATTRIBUTES:
            setattr(self.user, name, value)
        object.__setattr__(self, name, value)

    @property
    def is_fxa_migrated(self):
        return True

    @property
    def public_email(self):
        return False

    @property
    def avatar(self):
        return None

    @property
    def bio(self):
        return None

    @property
    def website(self):
        return None

    @property
    def twitter(self):
        return None

    @property
    def community_mozilla_org(self):
        return ""

    @property
    def people_mozilla_org(self):
        return ""

    @property
    def matrix_handle(self):
        return ""

    @property
    def timezone(self):
        return ZoneInfo(settings.TIME_ZONE)

    @property
    def country(self):
        return None

    @property
    def city(self):
        return None

    @property
    def first_answer_email_sent(self):
        return False

    @property
    def first_l10n_email_sent(self):
        return False

    @property
    def involved_from(self):
        return None

    @property
    def csat_email_sent(self):
        return None

    @property
    def fxa_password_change(self):
        return None

    @property
    def display_name(self):
        return self.name if self.name else self.user.username

    @property
    def products(self):
        return Product.objects.filter(codename__in=self.user.subscriptions)

    @property
    def is_subscriber(self):
        return self.products.exists()

    def save(self, update_fields=None):
        self.user.save()


class UserProxy:
    """An authenticated user without an account or profile"""

    GROUP_NAMES: set[str] = set()
    CACHE_KEY_PREFIX = "kitsune_user."

    _user_permissions = EmptyManager(Permission)

    @classmethod
    def cache(cls):
        return caches[settings.USER_CACHE_ALIAS]

    @classmethod
    def get_key(cls, fxa_uid):
        return f"{cls.CACHE_KEY_PREFIX}{fxa_uid}"

    @classmethod
    def get_user_from_key(cls, key):
        if key and (data := cls.cache.get(key)):
            return cls(**data)
        return None

    @classmethod
    def get_user_from_fxa_uid(cls, fxa_uid):
        return cls.get_user_from_key(cls.get_key(fxa_uid))

    def __init__(self, **attrs):
        for name, value in attrs.items():
            setattr(self, name, value)

    def __setattr__(self, name, value):
        """Clean and/or validate some attribute values before setting them."""
        if name == "email":
            value = BaseUserManager.normalize_email(value)
        elif name == "username":
            # Normalize and validate the username
            validate = UnicodeUsernameValidator()
            value = validate(unicodedata.normalize("NFKC", value))
        object.__setattr__(self, name, value)

    @property
    def key(self):
        return self.get_key(self.fxa_uid)

    @property
    def profile(self):
        return UserProxyProfile(self)

    def __str__(self):
        return self.username

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (vars(self) == vars(other))

    def __hash__(self):
        return hash(self.fxa_uid)

    def save(self, update_fields=None):
        self.cache.set(self.key, vars(self), timeout=settings.USER_CACHE_TIMEOUT)

    def delete(self):
        return self.cache.delete(self.key)

    @property
    def groups(self):
        return Group.objects.filter(name__in=self.GROUP_NAMES)

    @property
    def user_permissions(self):
        return self._user_permissions

    def get_user_permissions(self, obj=None):
        return set()

    def get_group_permissions(self, obj=None):
        if getattr(self, "_group_perm_cache", None) is None:
            perms = Permission.objects.filter(group__name__in=self.GROUP_NAMES).values_list(
                "content_type__app_label", "codename"
            )
            self._group_perm_cache = {f"{app_label}.{codename}" for app_label, codename in perms}
        return self._group_perm_cache

    def get_all_permissions(self, obj=None):
        return self.get_group_permissions(obj=obj)

    def has_perm(self, perm, obj=None):
        return perm in self.get_all_permissions(obj=obj)

    def has_perms(self, perm_list, obj=None):
        if not is_iterable(perm_list) or isinstance(perm_list, str):
            raise ValueError("perm_list must be an iterable of permissions.")
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        return any(perm[: perm.index(".")] == app_label for perm in self.get_all_permissions())

    @property
    def is_active(self):
        return True

    @property
    def is_staff(self):
        return False

    @property
    def is_superuser(self):
        return False

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def get_username(self):
        return self.username

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
