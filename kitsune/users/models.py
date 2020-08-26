import logging
import re
import time
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy
from timezone_field import TimeZoneField

from kitsune.lib.countries import COUNTRIES
from kitsune.products.models import Product
from kitsune.search.es_utils import UnindexMeBro
from kitsune.search.models import (
    SearchMappingType,
    SearchMixin,
    register_for_indexing,
    register_mapping_type,
)
from kitsune.sumo.models import LocaleField, ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import auto_delete_files
from kitsune.users.validators import TwitterValidator

log = logging.getLogger("k.users")


SHA1_RE = re.compile("^[a-f0-9]{40}$")
CONTRIBUTOR_GROUP = "Registered as contributor"
SET_ID_PREFIX = "https://schemas.accounts.firefox.com/event/"


@auto_delete_files
class Profile(ModelBase, SearchMixin):
    """Profile model for django users."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, verbose_name=_lazy("User")
    )
    name = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_lazy("Display name")
    )
    public_email = models.BooleanField(  # show/hide email
        default=False, verbose_name=_lazy("Make my email public")
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

    class Meta(object):
        permissions = (
            ("view_karma_points", "Can view karma points"),
            ("deactivate_users", "Can deactivate users"),
            ("screen_share", "Can screen share"),
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

    @property
    def twitter_usernames(self):
        from kitsune.customercare.models import Reply

        return list(
            Reply.objects.filter(user=self.user)
            .values_list("twitter_username", flat=True)
            .distinct()
        )

    @classmethod
    def get_mapping_type(cls):
        return UserMappingType

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
        from kitsune.customercare.models import Reply
        from kitsune.questions.models import Answer
        from kitsune.wiki.models import Revision

        dates = []

        # Latest Army of Awesome reply:
        try:
            aoa_reply = Reply.objects.filter(user=self.user).latest("created")
            dates.append(aoa_reply.created)
        except Reply.DoesNotExist:
            pass

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


@register_mapping_type
class UserMappingType(SearchMappingType):
    list_keys = [
        "twitter_usernames",
        "itwitter_usernames",
    ]

    @classmethod
    def get_model(cls):
        return Profile

    @classmethod
    def get_index_group(cls):
        return "non-critical"

    @classmethod
    def get_mapping(cls):
        return {
            "properties": {
                "id": {"type": "long"},
                "model": {"type": "string", "index": "not_analyzed"},
                "url": {"type": "string", "index": "not_analyzed"},
                "indexed_on": {"type": "integer"},
                "username": {"type": "string", "index": "not_analyzed"},
                "display_name": {"type": "string", "index": "not_analyzed"},
                "twitter_usernames": {"type": "string", "index": "not_analyzed"},
                "last_contribution_date": {"type": "date"},
                # lower-cased versions for querying:
                "iusername": {"type": "string", "index": "not_analyzed"},
                "idisplay_name": {"type": "string", "analyzer": "whitespace"},
                "itwitter_usernames": {"type": "string", "index": "not_analyzed"},
                "avatar": {"type": "string", "index": "not_analyzed"},
                "suggest": {"type": "completion", "analyzer": "whitespace", "payloads": True,},
            }
        }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        """Extracts interesting thing from a Thread and its Posts"""
        if obj is None:
            model = cls.get_model()
            obj = model.objects.select_related("user").get(pk=obj_id)

        if not obj.user.is_active:
            raise UnindexMeBro()

        d = {}
        d["id"] = obj.pk
        d["model"] = cls.get_mapping_type_name()
        d["url"] = obj.get_absolute_url()
        d["indexed_on"] = int(time.time())

        d["username"] = obj.user.username
        d["display_name"] = obj.display_name
        d["twitter_usernames"] = obj.twitter_usernames

        d["last_contribution_date"] = obj.last_contribution_date

        d["iusername"] = obj.user.username.lower()
        d["idisplay_name"] = obj.display_name.lower()
        d["itwitter_usernames"] = [u.lower() for u in obj.twitter_usernames]

        from kitsune.users.templatetags.jinja_helpers import profile_avatar

        d["avatar"] = profile_avatar(obj.user, size=120)

        d["suggest"] = {
            "input": [d["iusername"], d["idisplay_name"]],
            "output": _("{displayname} ({username})").format(
                displayname=d["display_name"], username=d["username"]
            ),
            "payload": {"user_id": d["id"]},
        }

        return d

    @classmethod
    def suggest_completions(cls, text):
        """Suggest completions for the text provided."""
        USER_SUGGEST = "user-suggest"
        es = UserMappingType.search().get_es()

        results = es.suggest(
            index=cls.get_index(),
            body={USER_SUGGEST: {"text": text.lower(), "completion": {"field": "suggest"}}},
        )

        if results[USER_SUGGEST][0]["length"] > 0:
            return results[USER_SUGGEST][0]["options"]

        return []


register_for_indexing("users", Profile)


def get_profile(u):
    try:
        return Profile.objects.get(user=u)
    except Profile.DoesNotExist:
        return None


register_for_indexing("users", User, instance_to_indexee=get_profile)


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

    activation_key_expired.boolean = True


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
