# Zendesk integration

## Authentication selection

Kitsune selects authentication from the configured credentials:

| Configuration | Authentication |
| --- | --- |
| Both `ZENDESK_OAUTH_CLIENT_ID` and `ZENDESK_OAUTH_CLIENT_SECRET` are non-empty | OAuth, even if legacy credentials are also configured |
| Either OAuth value is missing or empty | Legacy email + API token |

The legacy mechanism is HTTP Basic authentication with an email and an API token,
not a Zendesk password. Configure it with:

```text
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_USER_EMAIL=your-integration-account@example.com
ZENDESK_API_TOKEN=your-api-token
```

The selected method requires its complete credentials and a subdomain. Missing
credentials fail when an API operation is attempted. OAuth authentication errors
and timeouts never cause an automatic fallback to legacy credentials.

Run `./manage.py check` before deployment. Setting only one OAuth value emits
`customercare.W001`, warning that legacy authentication will be selected. Set both
values to enable OAuth, or clear both to select legacy authentication explicitly.

## OAuth setup

When OAuth is selected, Kitsune uses Zendesk's client-credentials flow. It obtains
an access token on the first API operation and caches it until one minute before
its reported expiry. Web and Celery workers reuse tokens through Django's default
cache; configure `CACHE_URL` to use their shared Redis cache.

In Zendesk Admin Center, under **Apps and integrations > APIs > OAuth clients**:

1. Create a **confidential** client for this integration and environment.
2. Set its allowed scopes to `read users:write tickets:write`.
3. Store its **Identifier** and **Secret** in the deployment's secret configuration:

   ```text
   ZENDESK_SUBDOMAIN=your-subdomain
   ZENDESK_OAUTH_CLIENT_ID=your-client-identifier
   ZENDESK_OAUTH_CLIENT_SECRET=your-client-secret
   ```

Client-credentials tokens act as the OAuth client's creator. Use the intended
integration account, with the permissions required to read tickets and users,
update users and email identities, and create or update tickets. No browser
callback or refresh token is needed.

### Rollout and rollback

Deploy the code with the existing legacy credentials and both OAuth values empty.
To enable OAuth, supply both OAuth values and restart or redeploy **both web and
Celery workers**. Django settings are loaded at process startup; this is not a
live switch. Legacy credentials may remain configured during the transition.

Verify ticket creation (authenticated and loginless), replies, synchronization,
and user updates in staging. To roll back, clear both OAuth values, ensure the
legacy email and API token are still configured and valid, and restart or redeploy
both web and Celery workers.

Revoke the old API token once the rollout is complete and no other integration
uses it. Legacy authentication is temporary: Zendesk retires API tokens on
April 30, 2027.

Webhook authentication and chat-widget signing credentials are separate and do
not change.

See [Zendesk's OAuth migration guide](https://developer.zendesk.com/documentation/authentication/oauth-migration/#client-credentials-grant)
for the client-credentials flow and token lifecycle.

## Using `requests` to query the API

During development being able to query the API manually to fetch details about field IDs,
user statuses,
and so on is very useful.

Use the authenticated `requests.Session` from `ZendeskClient` so manual requests
follow the same authentication selection as the application. For example, in
`./manage.py shell_plus`:

```python
from django.conf import settings

from kitsune.customercare.zendesk import ZendeskClient

base = f"https://{settings.ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/"
session = ZendeskClient().client.tickets.session

session.get(
    base + "ticket_fields.json",
    timeout=settings.ZENDESK_SYNC_TIMEOUT,
).json()

# For writes, replace the endpoint and payload with the intended operation.
session.post(
    base + "your_endpoint.json",
    json={},
    timeout=settings.ZENDESK_SYNC_TIMEOUT,
).json()
```

Create a fresh `ZendeskClient` and session for a new operation in a long-running
shell session rather than retaining an OAuth-authenticated session past its token
expiry. Do not print or log tokens or client secrets.
