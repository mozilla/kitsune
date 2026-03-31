import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from zenpy import Zenpy
from zenpy.lib.api_objects import Identity as ZendeskIdentity
from zenpy.lib.api_objects import Ticket
from zenpy.lib.api_objects import User as ZendeskUser

from kitsune.customercare.models import SupportTicket

NO_RESPONSE = "No response provided."
LOGINLESS_TAG = "loginless_ticket"


class ZendeskClient:
    """Client to connect to Zendesk API."""

    def __init__(self, **kwargs):
        """Initialize Zendesk API client."""
        creds = {
            "email": settings.ZENDESK_USER_EMAIL,
            "token": settings.ZENDESK_API_TOKEN,
            "subdomain": settings.ZENDESK_SUBDOMAIN,
        }
        self.client = Zenpy(**creds)
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(**Zenpy.http_adapter_kwargs()))
        self.session.auth = (f"{settings.ZENDESK_USER_EMAIL}/token", settings.ZENDESK_API_TOKEN)

    def _make_request(self, method, endpoint, data):
        """Make a direct request to the Zendesk REST API."""
        url = f"https://{settings.ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/{endpoint}"
        response = self.session.request(method, url, json=data)
        response.raise_for_status()
        return response.json()

    def _user_to_zendesk_user(self, user, email):
        """Given a Django user, return a Zendesk user."""
        # Four possible cases to account for:
        # 1. No Django User, No ZD User -> Create ZD User From Email
        # 2. No Django User, ZD User -> Get Existing ZD User Using Email
        # 3. Django User, No ZD User -> Create ZD User from Django User
        # 4. Django User, ZD User -> Get ZD User, Update Django User with Zendesk ID
        if not user or not user.is_authenticated:
            # If the user already exists in Zendesk return
            # the Zendesk user object
            # instead of creating a new one
            if zuser := self.get_user_by_email(email):
                # No Django user, but yes ZD user
                return zuser
            # No Django user, no ZD user
            name = "Anonymous User"
            locale = "en-US"
            id = None
            external_id = None
            user_fields = None
        # Yes Django user
        else:
            fxa_uid = user.profile.fxa_uid
            id_str = user.profile.zendesk_id
            id = int(id_str) if id_str else None  # Yes Or No ZD User
            name = user.profile.display_name
            locale = user.profile.locale
            user_fields = {"user_id": fxa_uid}
            external_id = fxa_uid
        return ZendeskUser(
            id=id,
            verified=True,
            email=email or user.email,
            name=name,
            locale=locale,
            user_fields=user_fields,
            external_id=external_id,
        )

    def get_user_by_email(self, email):
        """Given an email, return a user from Zendesk."""
        # This returns a generator, but we only want/expect one user
        # If it returns more than one, we should fail
        # Otherwise return the Zendesk user object
        search_results = self.client.search(type="user", query=f"email:{email}")

        user_found = None
        for user in search_results:
            if user_found is not None:
                raise ValueError(f"Found more than one user with email {email}")
            user_found = user

        return user_found

    def create_user(self, user, email=""):
        """Given a Django user, create a user in Zendesk."""
        zendesk_user = self._user_to_zendesk_user(user, email=email)
        # call create_or_update to avoid duplicating users FxA previously created
        zendesk_user = self.client.users.create_or_update(zendesk_user)

        # We can't save anything to AnonymousUser Profile
        # as it has none
        if user and user.is_authenticated:
            user.profile.zendesk_id = str(zendesk_user.id)
            user.profile.save(update_fields=["zendesk_id"])

        return zendesk_user

    def update_user(self, user):
        """Given a Django user, update a user in Zendesk."""
        zendesk_user = self._user_to_zendesk_user(user, email=user.email)
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
        custom_fields = [
            {"id": settings.ZENDESK_PRODUCT_FIELD_ID, "value": ticket_fields.get("product")},
            {"id": settings.ZENDESK_OS_FIELD_ID, "value": ticket_fields.get("os")},
            {"id": settings.ZENDESK_COUNTRY_FIELD_ID, "value": ticket_fields.get("country")},
        ]

        if ticket_fields.get("update_channel"):
            custom_fields.append(
                {
                    "id": settings.ZENDESK_UPDATE_CHANNEL_FIELD_ID,
                    "value": ticket_fields.get("update_channel"),
                }
            )

        if ticket_fields.get("policy_distribution"):
            custom_fields.append(
                {
                    "id": settings.ZENDESK_POLICY_DISTRIBUTION_FIELD_ID,
                    "value": ticket_fields.get("policy_distribution"),
                }
            )
        ticket_kwargs = {
            "subject": ticket_fields.get("subject")
            or f"{ticket_fields.get('product_title', 'Product')} support",
            "comment": {"body": ticket_fields.get("description") or str(NO_RESPONSE)},
            "ticket_form_id": ticket_fields.get("ticket_form_id"),
        }

        if brand_id := ticket_fields.get("brand_id"):
            ticket_kwargs["brand_id"] = int(brand_id)

        tags = []
        # If this is the normal, athenticated form we want to use the category field
        if user and user.is_authenticated:
            custom_fields.append(
                {"id": settings.ZENDESK_CATEGORY_FIELD_ID, "value": ticket_fields.get("category")},
            )
        # If this is the loginless form we want to use the contact label field (tag)
        # and fix the category field to be "accounts"
        else:
            custom_fields.extend(
                [
                    {
                        "id": settings.ZENDESK_CONTACT_LABEL_ID,
                        "value": ticket_fields.get("category"),
                    },
                    {"id": settings.ZENDESK_CATEGORY_FIELD_ID, "value": "accounts"},
                ]
            )
            tags.append(LOGINLESS_TAG)

        zendesk_tags = ticket_fields.get("zendesk_tags", [])
        if zendesk_tags:
            tags.extend(zendesk_tags)

        if tags:
            ticket_kwargs.update({"tags": tags})

        ticket_kwargs.update({"custom_fields": custom_fields})
        ticket = Ticket(**ticket_kwargs)

        if user and user.is_authenticated:
            if user.profile.zendesk_id:
                # TODO: is this necessary if we're
                # updating users as soon as they're updated locally?
                ticket.requester_id = self.update_user(user).id
            else:
                ticket.requester_id = self.create_user(user).id
        else:
            ticket.requester_id = self.create_user(user, email=ticket_fields.get("email", "")).id
        return self.client.tickets.create(ticket)

    def add_ticket_comment(self, ticket_id, comment_body, public=True, user=None):
        """Add a comment to a ticket via the Zendesk REST API.

        If a Django user is provided, the comment will be attributed to their
        corresponding Zendesk user. The user must have a zendesk_id set on their profile.
        """
        comment = {"body": comment_body, "public": public}
        if user:
            if not (user.is_authenticated and (zendesk_id := user.profile.zendesk_id)):
                raise ValueError(f'User "{user}" does not have a "zendesk_id".')
            comment["author_id"] = int(zendesk_id)
        data = {"ticket": {"comment": comment}}
        return self._make_request("PUT", f"tickets/{ticket_id}", data)

    def update_ticket_status(self, ticket_id, status):
        """Update a ticket's status via the Zendesk REST API."""
        if status not in SupportTicket.VALID_ZD_STATUSES:
            raise ValueError(
                f'Invalid status "{status}". Must be one of: '
                f"{', '.join(sorted(SupportTicket.VALID_ZD_STATUSES))}"
            )
        data = {"ticket": {"status": status}}
        return self._make_request("PUT", f"tickets/{ticket_id}", data)
