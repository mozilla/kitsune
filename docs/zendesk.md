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

## Ticket processing

New product and enterprise tickets store their accepted Zendesk configuration:
form, brand, product value, spam policy, and topic automation tags. Classification,
moderator release, and failed-ticket recovery use that snapshot even after
configuration changes; taxonomy tier and legacy tags still follow the current
Topic tree. Older product tickets without a snapshot use their live product
configuration. Missing enterprise context or a missing legacy configuration flags
the ticket for review rather than sending it.

Enterprise tickets belong to the contract's company and skip spam and product
reassignment checks, but still receive topic classification. Their origin adds
`seg-enterprise-support` to the outgoing Zendesk payload, not the stored tags.
Classification and moderator topic changes preserve system and `seg-*` tags.

Enterprise delivery explicitly sets the Zendesk organization linked to the accepted
company's external ID. Delivery requires a linked organization, an active requester
still in that SUMO company, and membership in its Zendesk organization. Missing any
of these holds the ticket with its snapshot unchanged. This covers departures before
remote removal, incomplete join synchronization, and membership removed directly in
Zendesk. Contract expiry alone does not block delivery. The sender never substitutes
another company/default organization or changes organization membership.

Holds and other send failures appear with notes in the staff **Zendesk Spam Queue**:

- **No spam found.** retries delivery and both membership checks; missing membership
  leaves the ticket pending in the queue.
- **Removed spam content.** rejects the ticket.

Synchronization does not release held tickets automatically. Membership checks and
remote ticket creation are not atomic; removal between checking and creation can race.

## Chat

Partially configured chat settings emit system-check warning `customercare.W002`;
with settings missing and the chat switch enabled, pages render without the widget
instead of failing, and authenticated token requests return HTTP 403.

## Enterprise provisioning

The [enterprise provisioning service](groups.md#enterprise-zendesk-provisioning)
and membership synchronization task use the authentication above. Their integration
account must also be allowed to create and delete organization memberships for end
users.

Organizations are linked by saved ID or created with `ZendeskOrganization.external_id`,
a stable local UUID, as the
[create-or-update key](https://developer.zendesk.com/api-reference/ticketing/organizations/organizations/#create-or-update-organization).
Provisioning and membership synchronization commit the local mapping and UUID before
any remote request, so a retry retains the same create-or-update identity. A 422 during
first creation is recovered only when a fresh external-ID lookup finds the same UUID
(case-insensitively); a name collision alone remains a conflict. Existing organizations
are not modified.

For provisioning and current-company synchronization, users are linked by saved ID
or invited email. Only active, unsuspended end users without elevated roles, whose
primary email and Mozilla identity match, are eligible; existing names and
identities are preserved. Users created for unclaimed accounts get no Mozilla
identity and skip the verification email; background profile synchronization leaves
their identity alone until first login attaches it.

Memberships use the
[Organization Memberships API](https://developer.zendesk.com/api-reference/ticketing/organizations/organization_memberships/#create-membership).
A 422 on creation counts as success only when a fresh read finds the target pair.
Provisioning and membership synchronization remove memberships only in other
organizations linked by `ZendeskOrganization.zendesk_id` or captured from deleted
company mappings, before ensuring that pair.
Members belong to at most one SUMO company organization. Organizations not linked to
SUMO, including agent-created ones, are untouched. For new joins, removal precedes
company membership creation to avoid rehoming former-company tickets into the new
company. If the target membership already exists, removing another SUMO-company
membership may move its open tickets into the company under Zendesk's behavior.
Both cases must be verified in a Zendesk sandbox.

Cleanup rejects elevated/shared Zendesk roles and remote identities owned by another
local account. It permits email, Mozilla identity, and active/suspended-status drift
when removing old company access. Captured cleanup removes only the supplied company
organization IDs. It preserves a surviving user's current company organization only
while that user's profile still owns the captured Zendesk user ID; otherwise it
removes the stale identity's captured memberships. Unrelated memberships are untouched.
Setup queues captured-pair cleanup when email/FxA identity changes or profile replacement
invalidate its resolved identity, even if the user stays in the same company. It does
not persist the invalidated link.

Remote requests use the account-email lock; hierarchy and row locks are limited to
local preparation and revalidation. Provider failures and local-state changes use
the existing task retries; permanent identity conflicts need administrator resolution.
For membership events, deletion and in-flight cleanup, and the existing-member
reconciliation command, see [membership mirroring](groups.md#membership-mirroring).

Profile Zendesk IDs must be canonical decimal strings, without whitespace or
leading zeros, so ownership checks match exactly; preserve this format in imports
and manual corrections. Apply `users.0040_profile_zendesk_id_index`, which builds
concurrently, before rolling out invited first login.

Requests use `ZENDESK_SYNC_TIMEOUT`, with SDK caching and rate-limit waits
disabled. Remote and local changes are not atomic: staff retry by rerunning the
service, and saved IDs, the organization UUID, and email lookup reconcile earlier
partial work. Zendesk search lag may require waiting before another attempt.
Identity conflicts or missing prepared resources need manual correction.

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
