from datetime import datetime, timedelta
from functools import cached_property

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models

from kitsune.wiki.models import Revision


LANGUAGE_CHOICES_EXCLUDING_DEFAULT = tuple(
    (lang, f"{settings.LOCALES[lang].english} ({lang})")
    for lang in settings.SUMO_LANGUAGES
    if lang not in ("xx", settings.WIKI_DEFAULT_LANGUAGE)
)


class MachineTranslationConfiguration(models.Model):
    is_enabled = models.BooleanField(default=False, verbose_name="Enable machine translation")
    llm_name = models.CharField(
        blank=True,
        max_length=100,
        verbose_name="LLM model name",
    )
    heartbeat_period = models.DurationField(
        default=timedelta(hours=4),
        verbose_name="Heartbeat period",
        help_text=(
            "The management of existing machine translations, as well as the "
            "generation of any new machine translations, will be performed at "
            "this interval."
        ),
    )
    review_grace_period = models.DurationField(
        default=timedelta(days=3),
        verbose_name="Review grace period",
        help_text=(
            "The grace period provided for the machine translation to be "
            "reviewed, after which it will be automatically approved."
        ),
    )
    post_review_grace_period = models.DurationField(
        default=timedelta(days=3),
        verbose_name="Post-review grace period",
        help_text=(
            "The grace period provided after the machine translation has "
            "been reviewed and rejected, after which the machine translation "
            "will be automatically approved if no other translation has been "
            "approved within that period."
        ),
    )
    locale_team_inactivity_grace_period = models.DurationField(
        default=timedelta(days=30),
        verbose_name="Locale-team inactivity grace period",
        help_text=(
            "If a leader or reviewer of a locale team has not created or "
            "reviewed a KB article within this period of time, the locale "
            "team will be considered inactive."
        ),
    )
    enabled_languages = models.JSONField(
        default=list, blank=True, help_text="The languages enabled for machine translation."
    )
    limit_to_slugs = models.JSONField(
        default=list,
        blank=True,
        help_text="Limit machine translation to these KB article slugs.",
    )
    disabled_slugs = models.JSONField(
        default=list,
        blank=True,
        help_text="Disable machine translation for these KB article slugs.",
    )
    limit_to_approved_after = models.DateTimeField(
        null=True,
        blank=True,
        default=datetime.now,
        verbose_name=(
            "Limit machine translation to KB article revisions approved "
            "after this date and time"
        ),
    )
    limit_to_approver_in_group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        default=None,
        related_name="+",
        on_delete=models.SET_DEFAULT,
        verbose_name=(
            "Limit machine translation to KB article revisions approved by "
            "users within this group"
        ),
    )

    class Meta:
        verbose_name = "Machine translation configuration"
        verbose_name_plural = "Machine translation configuration"

    @classmethod
    def load(cls):
        # Returns the singleton, creating it if necessary.
        instance, created = cls.objects.get_or_create(id=1)
        return instance

    @cached_property
    def limit_to_full_slugs(self):
        return set(slug for slug in self.limit_to_slugs if not slug.endswith("*"))

    @cached_property
    def limit_to_slug_prefixes(self):
        return tuple(slug.rstrip("*") for slug in self.limit_to_slugs if slug.endswith("*"))

    @cached_property
    def disabled_full_slugs(self):
        return set(slug for slug in self.disabled_slugs if not slug.endswith("*"))

    @cached_property
    def disabled_slug_prefixes(self):
        return tuple(slug.rstrip("*") for slug in self.disabled_slugs if slug.endswith("*"))

    def save(self, *args, **kwargs):
        # Check if an instance already exists in the database.
        if not self.pk and MachineTranslationConfiguration.objects.exists():
            raise ValidationError("Only one MachineTranslationConfiguration instance allowed.")
        return super().save(*args, **kwargs)

    def is_active(self):
        return self.is_enabled and self.llm_name and self.enabled_languages

    def is_slug_allowed(self, slug):
        """
        Returns True only if the slug is included and not excluded.
        """
        return (
            (not self.limit_to_slugs)
            or (slug in self.limit_to_full_slugs)
            or any(slug.startswith(p) for p in self.limit_to_slug_prefixes)
        ) and not (
            (slug in self.disabled_full_slugs)
            or any(slug.startswith(p) for p in self.disabled_slug_prefixes)
        )

    def is_approved_date_allowed(self, dtime):
        """
        Returns True only if there's no limit on the approval date or if the
        provided datetime instance is greater than the limit.
        """
        return (not self.limit_to_approved_after) or (dtime > self.limit_to_approved_after)

    def is_approver_allowed(self, user):
        """
        Returns True only if there's no limit on the approver or if the provided
        user is a member of the group to which approvers are limited to.
        """
        return (not self.limit_to_approver_in_group) or (
            user and user.groups.filter(id=self.limit_to_approver_in_group_id).exists()
        )

    def __str__(self):
        return "MachineTranslationConfiguration"


class MachineTranslationServiceRecord(models.Model):

    SERVICE_OPENAI_API = "openai-api"
    SERVICE_VERTEX_AI_API = "vertex-ai-api"

    SERVICES = (
        (SERVICE_OPENAI_API, "OpenAI API"),
        (SERVICE_VERTEX_AI_API, "Vertex AI API"),
    )

    created = models.DateTimeField(default=datetime.now)

    service = models.CharField(max_length=30, choices=SERVICES)

    model_name = models.CharField(max_length=50)

    target_locale = models.CharField(
        max_length=7,
        choices=LANGUAGE_CHOICES_EXCLUDING_DEFAULT,
    )

    source_revision = models.ForeignKey(
        Revision, on_delete=models.CASCADE, related_name="mt_service_records"
    )

    source_attribute = models.CharField(max_length=100)

    details = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["created"], name="created_idx"),
            models.Index(fields=["service"], name="service_idx"),
            models.Index(fields=["model_name"], name="model_name_idx"),
            models.Index(fields=["target_locale"], name="target_locale_idx"),
            models.Index(fields=["source_attribute"], name="source_attribute_idx"),
        ]


class RevisionActivityRecord(models.Model):

    MT_CREATED_AS_AWAITING_REVIEW = 0
    MT_CREATED_AS_APPROVED = 1
    MT_REJECTED = 2
    MT_APPROVED_PRE_REVIEW = 3
    MT_CREATED_AS_APPROVED_POST_REJECTION = 4

    ACTIONS = (
        (MT_CREATED_AS_AWAITING_REVIEW, "Created as awaiting review"),
        (MT_CREATED_AS_APPROVED, "Created as already approved"),
        (MT_REJECTED, "Rejected because no longer relevant"),
        (MT_APPROVED_PRE_REVIEW, "Approved because not reviewed within grace period"),
        (
            MT_CREATED_AS_APPROVED_POST_REJECTION,
            (
                "Created as already approved because nothing else approved within "
                "grace period after rejection"
            ),
        ),
    )

    revision = models.ForeignKey(
        Revision,
        on_delete=models.CASCADE,
        related_name="l10n_actions",
    )

    action = models.PositiveSmallIntegerField(choices=ACTIONS)

    class Meta:
        indexes = [
            models.Index(fields=["action"], name="action_idx"),
        ]

    @property
    def action_timestamp(self):
        if self.action in (self.MT_REJECTED, self.MT_APPROVED_PRE_REVIEW):
            return self.revision.reviewed
        return self.revision.created
