from dataclasses import dataclass

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import pgettext_lazy

from kitsune.groups.models import GroupProfile
from kitsune.products.models import Product, Topic
from kitsune.sumo.models import ModelBase


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

        user_paths = list(
            GroupProfile.objects.filter(group__user=user).values_list("path", flat=True)
        )
        accessible_orgs = [
            gp
            for gp in GroupProfile.objects.org_roots()
            if any(p.startswith(gp.path) for p in user_paths) or gp.can_moderate_group(user)
        ]
        return self.filter(Q(user=user) | Q(org_group__in=accessible_orgs))


class SupportTicket(ModelBase):
    """Model to store pending Zendesk ticket submissions before classification."""

    # Submission pipeline statuses
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FLAGGED = "flagged"
    STATUS_REJECTED = "rejected"
    STATUS_PROCESSING_FAILED = "processing_failed"

    SUBMISSION_STATUS_CHOICES = (
        (STATUS_PENDING, _lazy("Ticket Pending Classification")),
        (STATUS_SENT, _lazy("Ticket Sent")),
        (STATUS_FLAGGED, _lazy("Ticket under Review")),
        (STATUS_REJECTED, _lazy("Ticket Rejected")),
        (STATUS_PROCESSING_FAILED, _lazy("Ticket Processing Failed")),
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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="support_tickets")
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
            "Organization that owns this ticket for visibility purposes. Set "
            "automatically at submission to the nearest ancestor GroupProfile "
            "whose Group is in this product's hybrid_support_groups. Null means "
            "a personal ticket — visible only to the submitter."
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
    zd_updated_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    zd_deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set when the ticket is deleted in Zendesk (soft or permanent).",
    )
    comments = models.JSONField(default=list, blank=True)
    internal_zd_tags = models.JSONField(default=list, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = SupportTicketQuerySet.as_manager()

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Support Ticket: {self.subject} ({self.submission_status})"

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

    def get_absolute_url(self):
        if not self.user:
            return None
        return reverse("customercare.ticket_detail", args=[self.user.username, self.id])

    def can_reply(self, user):
        """Only the ticket owner may reply. Teammates who can view (see
        SupportTicketManager.accessible_to) must not, and a non-owner reply would
        also be misattributed to the owner in Zendesk."""
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
