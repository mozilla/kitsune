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
2. Set its allowed scopes to `read users:write tickets:write organizations:write`.
3. Store its **Identifier** and **Secret** in the deployment's secret configuration:

   ```text
   ZENDESK_SUBDOMAIN=your-subdomain
   ZENDESK_OAUTH_CLIENT_ID=your-client-identifier
   ZENDESK_OAUTH_CLIENT_SECRET=your-client-secret
   ```

Client-credentials tokens act as the OAuth client's creator. Use the intended
integration account, with the permissions required to read tickets, users, and
organizations, update users and email identities, and create or update tickets
and organizations. No browser callback or refresh token is needed.

Token cache keys include the requested scopes. When deploying expanded scopes,
update the OAuth client's allowed scopes first; narrower cached tokens will not
be reused.

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

## Enterprise provisioning

The [enterprise provisioning service](groups.md#enterprise-zendesk-provisioning)
uses the authentication above. Its integration account must also be allowed to
create organization memberships for end users.

Existing organization IDs are checked without changing names, identities, or
ticket-sharing policy. New organizations use `ZendeskOrganization.external_id`,
a stable local UUID, as the
[create-or-update key](https://developer.zendesk.com/api-reference/ticketing/organizations/organizations/#create-or-update-organization).
A matching name alone never adopts an organization.

User lookup uses the saved Zendesk ID when present, otherwise the invited email.
Before linking, it checks the primary email and known Mozilla identity. Only
active, unsuspended end users without elevated roles are eligible; existing names
and identities are preserved. New unclaimed users use the supplied first and last
names, have no fabricated identity, and set `verified=False` and
`skip_verify_email=True`. Duplicate-create failures are left for a later manual
retry, not an immediate second lookup. Ordinary background creation and profile
sync skip unclaimed invitation-created accounts without a Mozilla identity.
Successful first login attaches that identity to the same Zendesk user.

Profile Zendesk IDs must be canonical decimal strings, without whitespace or
leading zeros. Ownership checks use exact matches, including hidden profiles;
imports and manual corrections must preserve this format.
A non-unique partial index covers nonblank Zendesk IDs, allowing ownership
checks to avoid full-profile scans while account and hierarchy locks are held.
Apply `users.0040_profile_zendesk_id_index` before rolling out invited first
login; it builds this index concurrently.

Membership provisioning creates the requested pair through the
[Organization Memberships API](https://developer.zendesk.com/api-reference/ticketing/organizations/organization_memberships/#create-membership),
not user `organization_id` updates, which remove other memberships. A 422 succeeds
only when a fresh read confirms the exact target pair. Unrelated memberships and
their defaults are preserved rather than treated as conflicts.

Requests use `ZENDESK_SYNC_TIMEOUT`; SDK caching and rate-limit waits are disabled.
Staff retry by rerunning the fixed sequence. Stable organization UUIDs, saved IDs,
and email lookup reconcile lost responses and local rollbacks; Zendesk search lag
may require waiting before another attempt. There is no action checkpoint or
automatic retry policy.

Only the account-email lock spans provider requests; hierarchy and row locks are
taken afterward for fresh validation and persistence. Concurrently saved
organization/user links are accepted when they match this run's resolved remote
IDs, allowing different invitees to provision the same new company. Conflicting
company, account, mapping, or identity changes, or revoked permissions, stop local
writes rather than retargeting the results. Successful remote IDs can still be
recovered on a later valid attempt.

Remote writes and local changes are not atomic, and SUMO cannot lock concurrent
changes made directly in Zendesk. Identity conflicts or missing prepared resources
require manual correction rather than guessing or overwriting another account.

### Authenticated identity binding

`ZendeskClient.bind_user_identity(zendesk_id=..., fxa_uid=..., email=...)` attaches
a verified Mozilla identity to the saved end user. It checks the user's primary
email, role, and existing identity, and refuses when another Zendesk user already
owns the external ID. Callers check local ownership first.

Binding updates only `external_id` and `user_fields.user_id`, never upserting or
creating a user. Other custom fields are preserved, both identities are read back,
and replaying the same binding after a local rollback is safe.

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
