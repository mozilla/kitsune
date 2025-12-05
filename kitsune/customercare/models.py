from django.contrib.auth.models import User
from django.db import models

from kitsune.products.models import Product, Topic
from kitsune.sumo.models import ModelBase


class SupportTicket(ModelBase):
    """Model to store pending Zendesk ticket submissions before classification."""

    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FLAGGED = "flagged"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Ticket Pending Classification"),
        (STATUS_SENT, "Ticket Sent"),
        (STATUS_FLAGGED, "Ticket under Review"),
        (STATUS_REJECTED, "Ticket Rejected"),
    )

    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=255)
    email = models.EmailField()
    os = models.CharField(max_length=50, blank=True, default="")
    country = models.CharField(max_length=255, blank=True, default="")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="support_tickets")
    topic = models.ForeignKey(
        Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets"
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets"
    )
    zendesk_tags = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    zendesk_ticket_id = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Support Ticket: {self.subject} ({self.status})"
