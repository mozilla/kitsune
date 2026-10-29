# Zendesk integration

## Authentication selection

| Configuration | Authentication |
| --- | --- |
| Both `ZENDESK_OAUTH_CLIENT_ID` and `ZENDESK_OAUTH_CLIENT_SECRET` are non-empty | OAuth, even if legacy credentials are also configured |
| Either OAuth value is missing or empty | Legacy email + API token |

Legacy authentication is HTTP Basic with an email and an API token, not a Zendesk password:

```text
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_USER_EMAIL=your-integration-account@example.com
ZENDESK_API_TOKEN=your-api-token
```

The selected method needs its complete credentials and a subdomain; missing credentials
fail on the first API operation. OAuth errors and timeouts never fall back to legacy
credentials. Setting only one OAuth value emits `customercare.W001` (legacy will be used);
run `./manage.py check` before deploying, and set both values or clear both.

## OAuth setup

OAuth uses Zendesk's client-credentials flow. The token is fetched on the first API
operation and cached until a minute before it expires, in Django's default cache; set
`CACHE_URL` so web and Celery workers share it through Redis.

In Zendesk Admin Center, under Apps and integrations > APIs > OAuth clients:

1. Create a confidential client for this integration and environment.
2. Allow the scopes `read users:write tickets:write organizations:write`.
3. Store its identifier and secret in the deployment's secrets:

   ```text
   ZENDESK_SUBDOMAIN=your-subdomain
   ZENDESK_OAUTH_CLIENT_ID=your-client-identifier
   ZENDESK_OAUTH_CLIENT_SECRET=your-client-secret
   ```

Tokens act as the client's creator, so create it as the integration account. That account
needs to read tickets, users, and organizations, update users and email identities, and
create or update tickets and organizations. No browser callback or refresh token is
involved. Token cache keys include the scopes: when code requests more scopes, widen the
client's allowed scopes first, since narrower cached tokens aren't reused.

### Rollout and rollback

- Deploy with the existing legacy credentials and both OAuth values empty.
- To enable OAuth, set both values and restart or redeploy both web and Celery workers;
  settings load at startup, so this is not a live switch. Legacy credentials can stay
  configured meanwhile.
- In staging, verify ticket creation (authenticated and loginless), replies, sync, and user
  updates.
- To roll back, clear both OAuth values, make sure the legacy email and token are still
  valid, and restart both web and Celery workers.
- Once done, revoke the old API token if nothing else uses it. Zendesk retires API tokens
  on April 30, 2027.

Webhook authentication and chat-widget signing credentials are separate and unaffected.
See [Zendesk's OAuth migration guide](https://developer.zendesk.com/documentation/authentication/oauth-migration/#client-credentials-grant).

## Ticket processing

New product and enterprise tickets store their accepted Zendesk configuration: form,
brand, product value, spam policy, and topic automation tags. Classification, staff
release, and failed-ticket recovery use it even after configuration changes.

Behavior:

- Taxonomy tier and legacy tags still follow the current topic tree.
- Older product tickets without a stored configuration use the live one. A missing
  enterprise context or missing legacy configuration flags the ticket for review instead
  of sending it.
- Enterprise tickets skip spam and product reassignment checks but still get topic
  classification. Their origin adds `seg-enterprise-support` to the outgoing payload, not
  to the stored tags.
- Classification and topic changes by users with `customercare.change_supportticket` keep
  system and `seg-*` tags.

Enterprise delivery sets the Zendesk organization linked to the accepted company and
requires a linked organization, an active requester still in that company, the requester's
saved Zendesk user ID, and membership in the organization. Missing any of these holds the
ticket, its stored configuration unchanged.

Gotchas:

- Holds catch people who left before their Zendesk removal ran, incomplete join syncs, and
  memberships removed directly in Zendesk. Contract expiry alone doesn't block delivery.
- Only onboarding provisioning and membership sync create enterprise requesters or change
  memberships; delivery never substitutes another organization.
- Membership checks and ticket creation aren't atomic, so a removal in between can race.
- When Zendesk refuses a ticket with `RecordInvalid` or `UserSuspended`, an enterprise
  ticket is held and a product ticket rejected. Hold notes give a fixed reason, such as
  `Zendesk refused the ticket (UserSuspended)`, never the provider's text or personal data.

Holds and other send failures wait, with notes, in the staff Zendesk spam queue; only staff
can release or reject them. Releasing retries delivery and both membership checks, and a
still-missing membership leaves the ticket pending. Sync never releases held tickets.

## Chat

Who can chat and when chats are revoked: [Live chat](enterprise-support.md#live-chat).

Partial chat settings emit `customercare.W002`. With the chat switch on and settings
missing, pages render without the widget, authenticated token requests get HTTP 403, and
picking up a chat raises `ImproperlyConfigured` instead of recording a personal ticket.
`customercare.W003` reports the `zendesk-chat` switch on with all three chat settings empty;
it's a database check, so `./manage.py check --database default` and `migrate` report it.

## Enterprise provisioning

[Onboarding provisioning](enterprise-support.md#zendesk-provisioning) and membership sync use
the authentication above; their integration account must also be allowed to create and
delete organization memberships for end users.

Behavior:

- Organizations are linked by saved ID or created with `ZendeskOrganization.external_id`, a
  stable local UUID, as the
  [create-or-update key](https://developer.zendesk.com/api-reference/ticketing/organizations/organizations/#create-or-update-organization).
  The local mapping and UUID are committed before any create-or-update request, so a retry
  keeps the same identity. A linked organization is only read, never modified.
- Membership sync links users by saved ID or account email; provisioning by saved ID or the
  invited email. Only active, unsuspended end users without elevated roles, whose primary
  email and Mozilla identity match, are eligible; existing names and identities are kept.
- Users created by provisioning skip the verification email. Those for unclaimed accounts
  get no Mozilla identity, are left alone by background profile sync, and get it at first
  login.
- Memberships use the
  [Organization Memberships API](https://developer.zendesk.com/api-reference/ticketing/organizations/organization_memberships/#create-membership).
  Removal refuses a Zendesk user that another profile owns or that has an elevated or
  shared role, and tolerates email, Mozilla identity, and suspension drift. What is removed
  and when, retries, and recovery are in
  [Membership mirroring](enterprise-support.md#membership-mirroring).
- Requests use `ZENDESK_SYNC_TIMEOUT`, with SDK caching and rate-limit waits disabled.

Gotchas:

- Zendesk answers duplicates with 422. A 422 on first organization creation is accepted only
  when a fresh external-ID lookup finds the same UUID (case-insensitively), so a name
  collision stays a conflict. A 422 on membership creation counts as success only when a
  fresh read finds the target pair.
- Profile Zendesk IDs must be canonical decimal strings (no whitespace or leading zeros) so
  ownership checks match exactly; keep that format in imports and manual fixes.
- Zendesk search lags, so a retry may need to wait.

### Authenticated identity binding

`ZendeskClient.bind_user_identity(zendesk_id=..., fxa_uid=..., email=...)` attaches a
verified Mozilla identity to the saved end user. It checks the user's primary email, role,
and existing identity, and refuses when another Zendesk user already owns the external ID,
so callers check local ownership first. It updates only `external_id` and
`user_fields.user_id`, never creates or upserts a user, preserves other custom fields, and
reads both identities back.

## Using `requests` to query the API

To look up field IDs, user statuses, and similar details during development, use the
authenticated `requests.Session` from `ZendeskClient`, so manual requests use the same
authentication as the application. For example, in `./manage.py shell_plus`:

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

In a long-running shell, create a fresh `ZendeskClient` for each new operation rather than
keeping an OAuth session past its token expiry. Never print or log tokens or client secrets.
