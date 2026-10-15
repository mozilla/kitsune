from functools import cached_property
from hashlib import sha256
from typing import NoReturn

import requests
from django.conf import settings
from django.core.cache import cache
from zenpy import Zenpy
from zenpy.lib.api_objects import Comment as ZendeskComment
from zenpy.lib.api_objects import Identity as ZendeskIdentity
from zenpy.lib.api_objects import Organization as ZendeskOrganization
from zenpy.lib.api_objects import OrganizationMembership, Ticket
from zenpy.lib.api_objects import User as ZendeskUser
from zenpy.lib.exception import APIException, RecordNotFoundException, ZenpyException

from kitsune.customercare.models import SupportTicket

NO_RESPONSE = "No response provided."
LOGINLESS_TAG = "loginless_ticket"
CHAT_REVOKED_TAG = "chat-access-revoked"
OAUTH_SCOPES = "read users:write tickets:write organizations:write"
OAUTH_EXPIRY_MARGIN = 60


class ZendeskProvisioningConflict(Exception):
    """A permanent provisioning conflict described by a safe error code."""

    def __init__(self, code):
        if code not in (
            "account_conflict",
            "company_conflict",
            "resource_missing",
            "zendesk_conflict",
        ):
            code = "zendesk_conflict"
        self.code = code
        super().__init__(code)

    @classmethod
    def raise_from(cls, exc: APIException | requests.HTTPError) -> NoReturn:
        """Translate provider conflicts without wrapping other failures."""
        status = exc.response.status_code if exc.response is not None else None
        if isinstance(exc, RecordNotFoundException) or status == 404:
            raise cls("resource_missing") from exc
        if status in (400, 409, 422):
            raise cls("zendesk_conflict") from exc
        raise exc


def canonical_zendesk_id(value) -> str:
    """Validate and normalize a positive numeric Zendesk ID."""
    text = str(value)
    if not (text.isascii() and text.isdecimal() and len(text) <= 255):
        raise ZendeskProvisioningConflict("zendesk_conflict")
    number = int(text)
    if number <= 0:
        raise ZendeskProvisioningConflict("zendesk_conflict")
    return str(number)


def get_oauth_token():
    """Reuse the service token across web and Celery workers until near expiry."""
    subdomain = settings.ZENDESK_SUBDOMAIN
    client_id = settings.ZENDESK_OAUTH_CLIENT_ID
    client_secret = settings.ZENDESK_OAUTH_CLIENT_SECRET
    if not all((subdomain, client_id, client_secret)):
        raise ZenpyException("Zendesk OAuth requires a subdomain, client ID, and client secret.")

    # Invalidate cached credentials when the account, secret, or permissions change.
    identity = sha256(
        f"{subdomain}:{client_id}:{client_secret}:{OAUTH_SCOPES}".encode()
    ).hexdigest()
    cache_key = f"customercare:zendesk:oauth:{identity}"
    if token := cache.get(cache_key):
        return token

    response = requests.post(
        f"https://{subdomain}.zendesk.com/oauth/tokens",
        json={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": OAUTH_SCOPES,
        },
        timeout=settings.ZENDESK_SYNC_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    token = data["access_token"]
    cache.set(cache_key, token, timeout=max(0, data["expires_in"] - OAUTH_EXPIRY_MARGIN))
    return token


class ZendeskClient:
    """Client to connect to Zendesk API."""

    def __init__(self, **kwargs):
        # Bound every call so an unreachable/slow Zendesk can't hang a worker.
        kwargs.setdefault("timeout", settings.ZENDESK_SYNC_TIMEOUT)
        self._kwargs = kwargs

    @cached_property
    def client(self):
        # Fetch credentials inside the caller's API-operation error handling.
        if settings.ZENDESK_OAUTH_CLIENT_ID and settings.ZENDESK_OAUTH_CLIENT_SECRET:
            creds = {"oauth_token": get_oauth_token()}
        else:
            if not all(
                (
                    settings.ZENDESK_SUBDOMAIN,
                    settings.ZENDESK_USER_EMAIL,
                    settings.ZENDESK_API_TOKEN,
                )
            ):
                raise ZenpyException(
                    "Zendesk API token authentication requires a subdomain, user email, "
                    "and API token."
                )
            creds = {
                "email": settings.ZENDESK_USER_EMAIL,
                "token": settings.ZENDESK_API_TOKEN,
            }
        creds["subdomain"] = settings.ZENDESK_SUBDOMAIN
        return Zenpy(**(creds | self._kwargs))

    def validate_organization(self, zendesk_id: str) -> str:
        """Fetch an existing organization and return its canonical numeric ID."""
        organization_id = canonical_zendesk_id(zendesk_id)
        try:
            self.client.organizations(id=int(organization_id))
        except (APIException, requests.HTTPError) as exc:
            if isinstance(exc, RecordNotFoundException) or (
                exc.response is not None and exc.response.status_code == 404
            ):
                raise ZendeskProvisioningConflict("resource_missing") from exc
            raise
        return organization_id

    def ensure_organization(
        self, *, name: str, external_id: str, zendesk_id: str | None = None
    ) -> str:
        """Link a saved organization or provision using its stable local UUID."""
        try:
            if zendesk_id is not None:
                return self.validate_organization(zendesk_id)
            if not external_id:
                raise ZendeskProvisioningConflict("zendesk_conflict")
            organization = self.client.organizations.create_or_update(
                ZendeskOrganization(name=name, external_id=external_id)
            )
        except (APIException, requests.HTTPError) as exc:
            ZendeskProvisioningConflict.raise_from(exc)
        if (organization.external_id or "").casefold() != external_id.casefold():
            raise ZendeskProvisioningConflict("zendesk_conflict")
        return canonical_zendesk_id(organization.id)

    def validate_user(self, user, *, email, fxa_uid) -> str:
        """Only an active end user with matching identities can be linked."""
        if user.role != "end-user" or user.active is not True or user.suspended:
            raise ZendeskProvisioningConflict("account_conflict")
        if user.shared or user.shared_agent or user.chat_only or user.custom_role_id:
            raise ZendeskProvisioningConflict("account_conflict")
        if (user.email or "").casefold() != email.casefold():
            raise ZendeskProvisioningConflict("account_conflict")
        for remote_uid in (user.external_id, (user.user_fields or {}).get("user_id")):
            if remote_uid and (not fxa_uid or remote_uid != fxa_uid):
                raise ZendeskProvisioningConflict("account_conflict")
        return canonical_zendesk_id(user.id)

    def ensure_user(
        self,
        *,
        email: str,
        name: str,
        locale: str,
        fxa_uid: str | None = None,
        zendesk_id: str | None = None,
    ) -> str:
        """Reuse a saved or email-matched user without changing existing details."""
        try:
            if zendesk_id is not None:
                saved_id = canonical_zendesk_id(zendesk_id)
                user = self.client.users(id=int(saved_id))
                user_id: str | None = self.validate_user(user, email=email, fxa_uid=fxa_uid)
                if user_id != saved_id:
                    raise ZendeskProvisioningConflict("account_conflict")
                return user_id

            # Quote the email so it cannot introduce additional search terms.
            quoted_email = email.replace("\\", "\\\\").replace('"', '\\"')
            user_id = None
            for user in self.client.users.search(query=f'email:"{quoted_email}"'):
                matched_id = self.validate_user(user, email=email, fxa_uid=fxa_uid)
                if user_id is not None and user_id != matched_id:
                    raise ZendeskProvisioningConflict("account_conflict")
                user_id = matched_id
            if user_id is not None:
                return user_id

            fields = {}
            if fxa_uid:
                fields = {"external_id": fxa_uid, "user_fields": {"user_id": fxa_uid}}
            # Unlike an upsert, create cannot overwrite an identity won by a race.
            user = self.client.users.create(
                ZendeskUser(
                    email=email,
                    name=name,
                    locale=locale,
                    role="end-user",
                    verified=bool(fxa_uid),
                    skip_verify_email=True,
                    **fields,
                )
            )
        except (APIException, requests.HTTPError) as exc:
            ZendeskProvisioningConflict.raise_from(exc)
        return self.validate_user(user, email=email, fxa_uid=fxa_uid)

    def bind_user_identity(self, *, zendesk_id: str, fxa_uid: str, email: str) -> None:
        """Bind a verified Mozilla identity to an existing end user; never create one."""
        saved_id = canonical_zendesk_id(zendesk_id)
        try:
            remote = self.client.users(id=int(saved_id))
            if self.validate_user(remote, email=email, fxa_uid=fxa_uid) != saved_id:
                raise ZendeskProvisioningConflict("account_conflict")
            for owner in self.client.users(external_ids=[fxa_uid]):
                if canonical_zendesk_id(owner.id) != saved_id:
                    raise ZendeskProvisioningConflict("account_conflict")
            fields = {**(remote.user_fields or {}), "user_id": fxa_uid}
            self.client.users.update(
                ZendeskUser(id=int(saved_id), external_id=fxa_uid, user_fields=fields)
            )
            remote = self.client.users(id=int(saved_id))
        except (APIException, requests.HTTPError) as exc:
            ZendeskProvisioningConflict.raise_from(exc)
        if (
            self.validate_user(remote, email=email, fxa_uid=fxa_uid) != saved_id
            or remote.external_id != fxa_uid
            or (remote.user_fields or {}).get("user_id") != fxa_uid
        ):
            raise ZendeskProvisioningConflict("account_conflict")

    def ensure_organization_membership(self, *, user_id: str, organization_id: str) -> None:
        """Add the target membership without removing or replacing another company."""
        user_id = canonical_zendesk_id(user_id)
        organization_id = canonical_zendesk_id(organization_id)
        try:
            membership = self.client.organization_memberships.create(
                OrganizationMembership(user_id=int(user_id), organization_id=int(organization_id))
            )
        except (APIException, requests.HTTPError) as exc:
            if exc.response is not None and exc.response.status_code == 422:
                try:
                    for membership in self.client.users.organization_memberships(
                        user=int(user_id)
                    ):
                        if (
                            canonical_zendesk_id(membership.user_id) == user_id
                            and canonical_zendesk_id(membership.organization_id) == organization_id
                        ):
                            return
                except (APIException, requests.HTTPError) as read_exc:
                    ZendeskProvisioningConflict.raise_from(read_exc)
            ZendeskProvisioningConflict.raise_from(exc)
        if (
            canonical_zendesk_id(membership.user_id) != user_id
            or canonical_zendesk_id(membership.organization_id) != organization_id
        ):
            raise ZendeskProvisioningConflict("zendesk_conflict")

    def _user_to_zendesk_user(self, user, email):
        """Given a Django user, return a Zendesk user."""
        if not user or not user.is_authenticated:
            if zuser := self.get_user_by_email(email):
                return zuser
            name = "Anonymous User"
            locale = "en-US"
            id = None
            external_id = None
            user_fields = None
        else:
            fxa_uid = user.profile.fxa_uid
            id_str = user.profile.zendesk_id
            id = int(id_str) if id_str else None
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
        """Find one Zendesk user by email; reject ambiguous matches."""
        search_results = self.client.search(type="user", query=f"email:{email}")

        user_found = None
        for user in search_results:
            if user_found is not None:
                raise ValueError(f"Found more than one user with email {email}")
            user_found = user

        return user_found

    def get_user(self, zendesk_id):
        """Fetch a single Zendesk user by ID."""
        return self.client.users(id=int(zendesk_id))

    def create_user(self, user, email=""):
        """Given a Django user, create a user in Zendesk."""
        zendesk_user = self._user_to_zendesk_user(user, email=email)
        # call create_or_update to avoid duplicating users FxA previously created
        zendesk_user = self.client.users.create_or_update(zendesk_user)

        if user and user.is_authenticated:
            user.profile.zendesk_id = str(zendesk_user.id)
            user.profile.save(update_fields=["zendesk_id"])

        return zendesk_user

    def update_user(self, user):
        """Given a Django user, update a user in Zendesk."""
        zendesk_user = self._user_to_zendesk_user(user, email=user.email)
        return self.client.users.update(zendesk_user)

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
        if ticket_fields.get("urgency"):
            custom_fields.append(
                {
                    "id": settings.ZENDESK_URGENCY_FIELD_ID,
                    "value": ticket_fields.get("urgency"),
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

    def get_ticket(self, ticket_id):
        """Fetch a single ticket from Zendesk by ID."""
        return self.client.tickets(id=ticket_id)

    def get_ticket_comments(self, ticket_id):
        """Fetch all comments for a ticket from Zendesk."""
        return list(self.client.tickets.comments(ticket=ticket_id))

    def add_ticket_comment(self, user, ticket_id, comment_body, public=True, status=None):
        """Add a comment to a ticket in Zendesk.

        The comment will be attributed to the user's corresponding Zendesk user,
        which will be created if the user doesn't already have one. The user must
        be authenticated.

        If a status is given, the ticket's status is updated in the same call.
        """
        if not (user and user.is_authenticated):
            raise ValueError("Anonymous users are not allowed to comment.")

        if user.profile.zendesk_id:
            author_id = user.profile.zendesk_id
        else:
            author_id = self.create_user(user).id

        ticket = Ticket(id=ticket_id)
        if status:
            ticket.status = status
        ticket.comment = ZendeskComment(
            author_id=int(author_id),
            body=comment_body,
            public=public,
        )
        return self.client.tickets.update(ticket)

    def update_ticket_status(self, ticket_id, status):
        """Update a ticket's status in Zendesk."""
        ticket = Ticket(id=ticket_id, status=status)
        return self.client.tickets.update(ticket)

    def get_active_chat_tickets(self, zendesk_id):
        """Return the active live-chat tickets requested by the Zendesk user with this id.

        Takes a Zendesk user id rather than a Django user, so it still works after the
        user has been deleted.
        """
        active = SupportTicket.statuses_in_group(SupportTicket.ZD_GROUP_ACTIVE)
        return [
            ticket
            for ticket in self.client.users.requested(int(zendesk_id))
            if ticket.via.channel == SupportTicket.ZD_CHANNEL_MESSAGING and ticket.status in active
        ]

    def search_chat_tickets(self, created_after):
        """Return the live-chat tickets created after the given date.

        Uses the export search, which pages with a cursor and so, unlike the regular
        search, never stops at 1000 results.
        """
        return self.client.search_export(
            type="ticket", via=SupportTicket.ZD_CHANNEL_MESSAGING, created_after=created_after
        )

    def add_ticket_tags(self, ticket_id, tags):
        """Add tags to a ticket, keeping the tags it already has."""
        return self.client.tickets.add_tags(ticket_id, list(tags))
