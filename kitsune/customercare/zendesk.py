from django.conf import settings
from django.utils.translation import ugettext_lazy as _lazy
from zenpy import Zenpy
from zenpy.lib.api_objects import Identity as ZendeskIdentity
from zenpy.lib.api_objects import Ticket
from zenpy.lib.api_objects import User as ZendeskUser

# See docs/zendesk.md for details about getting the valid choice values for each field:
CATEGORY_CHOICES = [
    (None, _lazy("Select a topic")),
    ("payment", _lazy("Payments & Billing")),
    ("accounts", _lazy("Accounts & Login")),
    ("technical", _lazy("Technical")),
    ("feedback", _lazy("Provide Feedback/Request Features")),
    ("not_listed", _lazy("Not listed")),
]

OS_CHOICES = [
    (None, _lazy("Select platform")),
    ("win10", _lazy("Windows")),
    ("mac", _lazy("Mac OS")),
    ("linux", _lazy("Linux")),
    ("android", _lazy("Android")),
    ("ios", _lazy("iOS")),
    ("other", _lazy("Other")),
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

    def _user_to_zendesk_user(self, user, include_email=True):
        fxa_uid = user.profile.fxa_uid
        id_str = user.profile.zendesk_id
        return ZendeskUser(
            id=int(id_str) if id_str else None,
            verified=True,
            email=user.email if include_email else "",
            name=user.profile.display_name,
            locale=user.profile.locale,
            user_fields={"user_id": fxa_uid},
            external_id=fxa_uid,
        )

    def create_user(self, user):
        """Given a Django user, create a user in Zendesk."""
        zendesk_user = self._user_to_zendesk_user(user)
        # call create_or_update to avoid duplicating users FxA previously created
        zendesk_user = self.client.users.create_or_update(zendesk_user)

        user.profile.zendesk_id = str(zendesk_user.id)
        user.profile.save(update_fields=["zendesk_id"])

        return zendesk_user

    def update_user(self, user):
        """Given a Django user, update a user in Zendesk."""
        zendesk_user = self._user_to_zendesk_user(user, include_email=False)
        zendesk_user = self.client.users.update(zendesk_user)
        return zendesk_user

    def get_primary_email_identity(self, zendesk_user_id):
        """Fetch the identity with the primary email from Zendesk"""

        for identity in self.client.users.identities(id=zendesk_user_id):
            if identity.primary and identity.type == "email":
                return identity.id

    def update_primary_email(self, zendesk_user_id, email):
        """Update the primary email of the user."""
        identity_id = self.get_primary_email_identity(zendesk_user_id)
        self.client.users.identities.update(
            user=zendesk_user_id, identity=ZendeskIdentity(id=identity_id, value=email)
        )

    def create_ticket(self, user, ticket_fields):
        """Create a ticket in Zendesk."""
        ticket = Ticket(
            subject=ticket_fields.get("subject"),
            comment={"body": ticket_fields.get("description")},
            ticket_form_id=settings.ZENDESK_TICKET_FORM_ID,
            custom_fields=[
                {"id": settings.ZENDESK_PRODUCT_FIELD_ID, "value": ticket_fields.get("product")},
                {"id": settings.ZENDESK_CATEGORY_FIELD_ID, "value": ticket_fields.get("category")},
                {"id": settings.ZENDESK_OS_FIELD_ID, "value": ticket_fields.get("os")},
                {"id": settings.ZENDESK_COUNTRY_FIELD_ID, "value": ticket_fields.get("country")},
            ],
        )
        if user.profile.zendesk_id:
            # TODO: is this necessary if we're updating users as soon as they're updated locally?
            ticket.requester_id = self.update_user(user).id
        else:
            ticket.requester_id = self.create_user(user).id
        return self.client.tickets.create(ticket)
