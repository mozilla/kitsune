from django.conf import settings
from zenpy import Zenpy
from zenpy.lib.api_objects import User as ZendeskUser


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

    def _get_zendesk_user_attrs(self, user):
        return {"email": user.email, "name": user.profile.name, "verified": True}

    def get_user(self, **kwargs):
        """Return a user from Zendesk."""
        raise NotImplementedError

    def update_user(self, **kwargs):
        """Update a user in Zendesk."""
        raise NotImplementedError

    def get_or_create_user(self, user):
        """Given a Django user, get or create a user in Zendesk."""
        # TODO: probably replace user with request.user and get also the locale from there

        zendesk_user = ZendeskUser(**self._get_zendesk_user_attrs(user))
        zen_user = self.client.users.create_or_update(zendesk_user)
        user.profile.zendesk_id = str(zen_user.id)
        user.profile.save()

    def create_ticket(self, **kwargs):
        """Create a ticket in Zendesk."""
        raise NotImplementedError

    def get_ticket(self, **kwargs):
        """Get a ticket from Zendesk."""
        raise NotImplementedError
