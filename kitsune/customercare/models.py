import uuid
from dataclasses import dataclass

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.functions import Substr
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import pgettext_lazy

from kitsune.groups.models import GroupProfile
from kitsune.products import PRODUCT_SLUG_ALIASES
from kitsune.products.models import Product, ProductSupportConfig, Topic
from kitsune.sumo.models import ModelBase

ZENDESK_PRODUCT_SLUGS = {v: k for k, v in PRODUCT_SLUG_ALIASES.items()}


class MissingTicketContext(Exception):
    pass


def accepted_context_for(product, zendesk_config, coverage=None, *, topics=None) -> dict:
    if topics is None:
        topics = zendesk_config.topics.filter(topic__isnull=False)
    automation_tags: dict[str, list[str]] = {}
    for topic in sorted(topics, key=lambda topic: topic.slug):
        if topic.topic_id is not None:
            automation_tags.setdefault(str(topic.topic_id), topic.automation_tags)
    context = {
        "form_id": zendesk_config.ticket_form_id,
        "brand_id": zendesk_config.brand_id,
        "product_value": (
            ZENDESK_PRODUCT_SLUGS.get(product.slug, product.slug)
            if product.slug == "mozilla-vpn"
            else product.slug
        ),
        "skip_spam": zendesk_config.skip_spam_moderation,
        "automation_tags": automation_tags,
    }
    if coverage:
        company = coverage.contract.company
        organization, _ = ZendeskOrganization.objects.get_or_create(group_profile=company)
        context.update(
            product_value=coverage.zendesk_product_value,
            skip_spam=True,
            coverage_id=coverage.pk,
            contract={"id": coverage.contract_id, "name": coverage.contract.name},
            company={"external_id": str(organization.external_id), "name": company.group.name},
        )
    return context


class ZendeskOrganization(ModelBase):
    """Company-wide identity shared by its product support configurations."""

    group_profile = models.OneToOneField(
        GroupProfile, on_delete=models.CASCADE, related_name="zendesk_organization"
    )
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    zendesk_id = models.CharField(max_length=255, unique=True, null=True, blank=True)


@dataclass(frozen=True)
class StatusMeta:
    """Display metadata for a single Zendesk ticket status.

    group   -- the "active" or "solved" bucket the status belongs to; drives the
               SupportTicketQuerySet.active()/solved() filters.
    variant -- the status-label--<variant> modifier for the badge; the colors for
               each variant live in SCSS (base/_status-label.scss).
    tip     -- the tooltip copy shown on the badge.
    """

    group: str
    variant: str
    tip: str


class SupportTicketQuerySet(models.QuerySet):
    def syncable(self):
        # Mirror SupportTicket.is_syncable: a usable Zendesk id and not deleted.
        return self.filter(zd_deleted_at__isnull=True).exclude(
            Q(zendesk_ticket_id__isnull=True) | Q(zendesk_ticket_id="")
        )

    def active(self):
        # Display semantics: status alone, regardless of whether the ticket has
        # synced a Zendesk id yet. Chain .syncable() when sync-eligibility matters.
        return self.filter(
            zd_status__in=SupportTicket.statuses_in_group(SupportTicket.ZD_GROUP_ACTIVE),
            zd_deleted_at__isnull=True,
        )

    def solved(self):
        return self.filter(
            zd_status__in=SupportTicket.statuses_in_group(SupportTicket.ZD_GROUP_SOLVED),
            zd_deleted_at__isnull=True,
        )

    def accessible_to(self, user):
        if not (user and user.is_authenticated):
            return self.none()
        if user.is_staff or user.is_superuser:
            return self.all()

        accessible_orgs = (
            GroupProfile.objects.org_roots()
            .alias(root_path=Substr("path", 1, GroupProfile.steplen))
            .filter(
                Q(pk__in=GroupProfile.objects.containing(user))
                | Q(leaders=user)
                | Q(
                    root_path__in=GroupProfile.objects.filter(depth=1, leaders=user).values("path")
                )
            )
        )
        return self.filter(Q(user=user) | Q(org_group__in=accessible_orgs))


class SupportTicket(ModelBase):
    """Model to store pending Zendesk ticket submissions before classification."""

    class Origin(models.TextChoices):
        PRODUCT = "product", _lazy("Product support")
        ENTERPRISE = "enterprise", _lazy("Enterprise support")

    # Submission pipeline statuses
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FLAGGED = "flagged"
    STATUS_REJECTED = "rejected"
    STATUS_PROCESSING_FAILED = "processing_failed"

    SUBMISSION_STATUS_CHOICES = (
        (STATUS_PENDING, "Ticket Pending Classification"),
        (STATUS_SENT, "Ticket Sent"),
        (STATUS_FLAGGED, "Ticket under Review"),
        (STATUS_REJECTED, "Ticket Rejected"),
        (STATUS_PROCESSING_FAILED, "Ticket Processing Failed"),
    )

    # Zendesk ticket lifecycle statuses.
    # "pending" means the ticket is awaiting a response from the customer.
    # "hold" means the ticket is awaiting a response from a third party.
    ZD_STATUS_NEW = "new"
    ZD_STATUS_OPEN = "open"
    ZD_STATUS_PENDING = "pending"
    ZD_STATUS_HOLD = "hold"
    ZD_STATUS_SOLVED = "solved"
    ZD_STATUS_CLOSED = "closed"

    ZD_STATUS_CHOICES = (
        # L10n: This is a support ticket status.
        (ZD_STATUS_NEW, pgettext_lazy("ticket", "New")),
        # L10n: This is a support ticket status.
        (ZD_STATUS_OPEN, pgettext_lazy("ticket", "Open")),
        # L10n: This is a support ticket status, which means the ticket is awaiting a response from the customer.
        (ZD_STATUS_PENDING, pgettext_lazy("ticket", "Pending")),
        # L10n: This is a support ticket status, which means the ticket is awaiting a response from a third party.
        (ZD_STATUS_HOLD, _lazy("Hold")),
        # L10n: This is a support ticket status.
        (ZD_STATUS_SOLVED, pgettext_lazy("ticket", "Solved")),
        # L10n: This is a support ticket status.
        (ZD_STATUS_CLOSED, _lazy("Closed")),
    )

    ZD_GROUP_ACTIVE = "active"
    ZD_GROUP_SOLVED = "solved"

    ZD_CHANNEL_MESSAGING = "native_messaging"

    # Per-status metadata. The group is the active/solved bucket for the status,
    # and defines the single source of truth for the split (no second hardcoded
    # list in the querysets). The variant selects the appropriate CSS variant,
    # and the tip is the visual tool tip for the status.
    ZD_STATUS_META = {
        ZD_STATUS_NEW: StatusMeta(
            group=ZD_GROUP_ACTIVE,
            variant="new",
            tip=_lazy("This ticket has been received and is awaiting review"),
        ),
        ZD_STATUS_OPEN: StatusMeta(
            group=ZD_GROUP_ACTIVE,
            variant="open",
            tip=_lazy("This ticket is open and being reviewed by our team"),
        ),
        ZD_STATUS_PENDING: StatusMeta(
            group=ZD_GROUP_ACTIVE,
            variant="pending",
            tip=_lazy("Our team has responded and is awaiting a reply"),
        ),
        ZD_STATUS_HOLD: StatusMeta(
            group=ZD_GROUP_ACTIVE,
            variant="hold",
            tip=_lazy("Our team is investigating with a third party"),
        ),
        ZD_STATUS_SOLVED: StatusMeta(
            group=ZD_GROUP_SOLVED,
            variant="solved",
            tip=_lazy("This ticket has been resolved"),
        ),
        ZD_STATUS_CLOSED: StatusMeta(
            group=ZD_GROUP_SOLVED,
            variant="closed",
            tip=_lazy("This ticket has been closed"),
        ),
    }

    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=255)
    email = models.EmailField()
    os = models.CharField(max_length=50, blank=True, default="")
    country = models.CharField(max_length=255, blank=True, default="")
    update_channel = models.CharField(max_length=100, blank=True, default="")
    policy_distribution = models.CharField(max_length=255, blank=True, default="")
    urgency = models.CharField(max_length=50, blank=True, default="")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="support_tickets")
    origin = models.CharField(max_length=20, choices=Origin.choices, default=Origin.PRODUCT)
    coverage = models.ForeignKey(
        "products.SupportCoverage",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    accepted_context = models.JSONField(default=dict, blank=True)
    topic = models.ForeignKey(
        Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets"
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets"
    )
    org_group = models.ForeignKey(
        "groups.GroupProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
        db_index=True,
        help_text=(
            "Company that owns an enterprise ticket, set at acceptance. "
            "Legacy tickets retain their original support organization. "
            "Null means a personal ticket, visible only to the submitter."
        ),
    )
    zendesk_tags = models.JSONField(default=list, blank=True)
    submission_status = models.CharField(
        max_length=20,
        choices=SUBMISSION_STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    zendesk_ticket_id = models.CharField(max_length=255, null=True, blank=True)
    zd_status = models.CharField(max_length=20, choices=ZD_STATUS_CHOICES, null=True, blank=True)
    zd_channel = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Zendesk channel the ticket was created via (e.g., native_messaging)",
    )
    zd_updated_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    zd_deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set when the ticket is deleted in Zendesk (soft or permanent).",
    )
    comments = models.JSONField(default=list, blank=True)
    internal_zd_tags = models.JSONField(default=list, blank=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)

    objects = SupportTicketQuerySet.as_manager()

    class Meta:
        ordering = ["-created"]
        constraints = [
            # One SupportTicket per Zendesk ticket. Tickets not yet sent to Zendesk
            # have no id, so they're left out.
            models.UniqueConstraint(
                fields=["zendesk_ticket_id"],
                condition=Q(zendesk_ticket_id__isnull=False) & ~Q(zendesk_ticket_id=""),
                name="unique_zendesk_ticket_id",
            ),
        ]

    def __str__(self):
        return f"Support Ticket: {self.subject} ({self.submission_status})"

    @property
    def context(self) -> dict:
        """Stored accepted context; older product tickets use the live product config."""
        if self.accepted_context:
            return self.accepted_context
        if self.origin == self.Origin.ENTERPRISE:
            raise MissingTicketContext(f"Enterprise ticket {self.pk} has no accepted context")
        config = ProductSupportConfig.objects.active_for(self.product)
        if not config or not config.zendesk_config:
            raise MissingTicketContext(
                f"Product ticket {self.pk} has no accepted context or active Zendesk config"
            )
        return accepted_context_for(self.product, config.zendesk_config)

    @property
    def title(self):
        return self.subject

    @property
    def content(self):
        return self.description

    @property
    def channel(self):
        return "direct_support"

    @property
    def is_syncable(self):
        """True if the ticket can be synced with Zendesk."""
        return bool(self.zendesk_ticket_id and not self.zd_deleted_at)

    @property
    def is_chat(self):
        """True if the ticket started as a live chat in the messaging widget."""
        return self.zd_channel == self.ZD_CHANNEL_MESSAGING

    def get_absolute_url(self):
        if not self.user:
            return None
        return reverse("customercare.ticket_detail", args=[self.user.username, self.id])

    def can_reply(self, user):
        """Only the ticket owner may reply. Teammates who can view (see
        SupportTicketManager.accessible_to) must not, and a non-owner reply would
        also be misattributed to the owner in Zendesk."""
        if self.is_chat:
            return False
        return bool(user and user.is_authenticated and self.user_id == user.id)

    @property
    def num_answers(self):
        return len(self.public_comments)

    @property
    def public_comments(self):
        # Zendesk always stores the ticket's description as the first comment, but
        # if the ticket hasn't yet been synchronized with Zendesk, the first comment
        # would be a webhook-appended reply.
        first_reply_index = 0 if self.last_synced_at is None else 1
        return [c for c in self.comments[first_reply_index:] if c.get("public", False)]

    @classmethod
    def statuses_in_group(cls, group):
        """The zd_status values belonging to an active/solved group."""
        return tuple(status for status, meta in cls.ZD_STATUS_META.items() if meta.group == group)

    @property
    def status_meta(self):
        """Display metadata for the current zd_status, or None for a status not in
        the registry (e.g. a not-yet-synced ticket whose zd_status is null)."""
        return self.ZD_STATUS_META.get(self.zd_status)

    @property
    def status_label(self):
        """Derive a user-facing status."""
        if self.zd_deleted_at:
            return _lazy("Inactive")
        return self.get_zd_status_display() or _lazy("Submitted")

    @property
    def status_variant(self):
        """The status-label--<variant> modifier for this ticket's badge. Deleted
        and not-yet-synced tickets fall back to the "neutral" variant."""
        if self.zd_deleted_at:
            return "neutral"
        meta = self.status_meta
        return meta.variant if meta else "neutral"

    @property
    def status_tip(self):
        """Tooltip copy describing the ticket's current status."""
        if self.zd_deleted_at:
            return _lazy("This ticket is no longer active and can no longer receive replies")
        meta = self.status_meta
        if meta:
            return meta.tip
        return _lazy("This ticket has been submitted and is being processed")
