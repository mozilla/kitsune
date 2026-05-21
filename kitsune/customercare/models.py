from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _lazy

from kitsune.products.models import Product, Topic
from kitsune.sumo.models import ModelBase


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
        (ZD_STATUS_NEW, _lazy("New")),
        (ZD_STATUS_OPEN, _lazy("Open")),
        (ZD_STATUS_PENDING, _lazy("Pending")),
        (ZD_STATUS_HOLD, _lazy("Hold")),
        (ZD_STATUS_SOLVED, _lazy("Solved")),
        (ZD_STATUS_CLOSED, _lazy("Closed")),
    )

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
    comments = models.JSONField(default=list, blank=True)
    internal_zd_tags = models.JSONField(default=list, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

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

    def get_absolute_url(self):
        if not self.user:
            return None
        return reverse("customercare.ticket_detail", args=[self.user.username, self.id])

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

    @property
    def user_status(self):
        """Derive a user-facing status from submission_status and zd_status."""
        if self.submission_status == self.STATUS_REJECTED:
            return None
        if self.submission_status in (
            self.STATUS_PENDING,
            self.STATUS_FLAGGED,
            self.STATUS_PROCESSING_FAILED,
        ):
            return _lazy("processing")
        # STATUS_SENT — delegate to ZD status if available
        return self.zd_status or _lazy("submitted")
