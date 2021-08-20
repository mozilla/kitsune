from django.conf import settings
from django.utils.translation import ugettext_lazy as _lazy
from zenpy import Zenpy
from zenpy.lib.api_objects import User as ZendeskUser, Ticket

TICKET_FORM_ID = 360000417171

# See docs/zendesk.md for details about getting the valid choice values for each field:

PRODUCT_FIELD_ID = 360047198211

CATEGORY_FIELD_ID = 360047206172
CATEGORY_CHOICES = [
    ("technical", _lazy("Technical")),
    ("accounts", _lazy("Accounts & Login")),
    ("payments", _lazy("Payment & Billing")),
    ("troubleshooting", _lazy("Troubleshooting")),
]

OS_FIELD_ID = 360018604871
OS_CHOICES = [
    (None, ""),
    ("win10", _lazy("Windows")),
    ("android", _lazy("Android")),
    ("linux", _lazy("Linux")),
    ("web", _lazy("Web")),
    ("mac", _lazy("Mac OS")),
    ("win8", _lazy("Windows 8")),
]


class ZendeskClient(object):
    """Client to connect to Zendesk API."""

    def __init__(self, **kwargs):
        """Initialize Zendesk API client."""
        creds = {
            "email": settings.ZENDESK_USER_EMAIL,
            "token": settings.ZENDESK_API_TOKEN,
            "subdomain": settings.ZENDESK_SUBDOMAIN,
        }
        self.client = Zenpy(**creds)

    def create_or_update_user(self, user):
        """Given a Django user, get or create a user in Zendesk."""
        fxa_uid = user.profile.fxa_uid
        zendesk_user = ZendeskUser(
            verified=True,
            email=user.email,
            name=user.profile.display_name,
            locale=user.profile.locale,
            user_fields={"user_id": fxa_uid},
            external_id=fxa_uid,
        )
        zendesk_user = self.client.users.create_or_update(zendesk_user)

        user.profile.zendesk_id = str(zendesk_user.id)
        user.profile.save()

        return zendesk_user.id

    def create_ticket(
        self, user, subject="", description="", product="", category="", os="", **kwargs
    ):
        """Create a ticket in Zendesk."""
        ticket = Ticket(
            subject=subject,
            comment={"body": description},
            ticket_form_id=TICKET_FORM_ID,
            custom_fields=[
                {"id": PRODUCT_FIELD_ID, "value": product},
                {"id": CATEGORY_FIELD_ID, "value": category},
                {"id": OS_FIELD_ID, "value": os},
            ],
        )
        ticket.requester_id = self.create_or_update_user(user)
        return self.client.tickets.create(ticket)
