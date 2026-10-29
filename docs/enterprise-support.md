# Enterprise support

Companies buy professional support through contracts. Members of a covered company get a
dedicated Zendesk ticket form for the covered products, ticket history shared with their
company, and optionally live chat. Staff onboard people into a company and its Zendesk
organization. Access follows contracts and membership: it ends when a contract ends or a
person leaves.

Code: groups and onboarding in `kitsune/groups`, contracts and routing in
`kitsune/products` (`routing.py` decides what a user gets for a product), tickets, chat, and
the Zendesk client in `kitsune/customercare`. Zendesk-side details are in
[Zendesk](zendesk.md).

## Hierarchy and membership

```
professional-support (root, ENTERPRISE_GROUP_SLUG)
├── Acme (company)
│   ├── Engineering (department)
│   │   └── Platform (department)
│   └── Sales (department)
└── Globex (company)
```

Companies are the root's direct children; departments are any deeper groups. A user
belongs to at most one company, through the company group or any of its departments.

Behavior:

- Several departments of one company are allowed. Company and root membership are never
  added implicitly, and staff and superusers get no exception.
- Root membership, leadership, and staff status don't make anyone a company member.
- Member and leader controls, admin membership changes, and leader assignment (which also
  grants membership) enforce the one-company rule; a conflicting batch is rejected whole.
  Moving groups or changing their Django groups is refused if it would put a user in two
  companies. Errors never name another private company.

Gotchas:

- `ENTERPRISE_GROUP_SLUG` (default `professional-support`) must match the root group's slug.
  If they differ, no company is recognized and enterprise support is off.
- Direct writes to the membership tables bypass every safeguard; use the normal
  group-management paths.
- Existing conflicts aren't repaired automatically. Removals always work, so an
  administrator can resolve them.
- A company's or department's Django group must not also back a group outside the tree:
  membership added there makes the user a company member.

## Company setup

Operators create companies and link a company to an existing Zendesk organization.
Operators are active staff who lead the root or are superusers; company leadership doesn't
count.

Behavior:

- Setup acts only on the root and its direct children, never departments or other
  hierarchies, and never changes membership or leadership. Read-only mode refuses it.
- The root must be PRIVATE or MODERATED with sibling isolation. New companies inherit its
  visibility.
- Company names and generated slugs must be unused; collisions are rejected, never
  suffixed.
- An optional Zendesk organization ID is verified in Zendesk before linking; a blank ID
  creates nothing in Zendesk. Errors leave everything unchanged.
- An organization belongs to one company, a saved link can't be reassigned, linking can't
  rename the company, and a name never adopts an existing organization.
- No product support configuration is needed for setup or invitations.

## Contracts and coverage

Staff record agreements in Django admin. A contract has a status (active, suspended, or
cancelled) and start and end dates, both inclusive in the site time zone. Each coverage
names a product, its Zendesk form configuration, the Zendesk product value, and whether
chat is included; a bundle is several coverages on one contract.

Behavior:

- The contract's company must be a direct child of the root and is read-only after the
  first save.
- A contract needs at least one coverage and lists each product once. A saved coverage's
  product can't change; its Zendesk configuration and product value can.
- Active and suspended contracts of a company can't cover the same product in overlapping
  periods; cancelled ones never block.
- Admin can't delete contracts or coverages. Cancel to retire one; to fix a mistake, cancel
  it and enter a new one.
- A company with contracts, in any status, can't be deleted, moved from under the root, or
  given another Django group in admin.

### Effective coverage

A user has effective coverage of a product when an active contract of their company covers
it and today is within its dates. It selects the enterprise form at
`/questions/new/<product>/form`, ahead of any product ticket.

Behavior:

- No enterprise support for inactive users, members of two companies, archived products,
  or products with more than one effective coverage.
- No product support configuration is needed, and the product's subscription requirement
  doesn't apply.
- Covered users get no personal-ticket form for that product; a forum they can use stays
  available.

## Live chat

A user can chat about a product when the `zendesk-chat` switch is on,
`ZENDESK_CHAT_WIDGET_KEY`, `ZENDESK_CHAT_SIGNING_SECRET`, and `ZENDESK_CHAT_SIGNING_KEY_ID`
are set, and their effective coverage of the product includes chat. The router, chat widget,
chat token signing, and chat-ticket adoption all use this one rule (`resolve_chat`).

Behavior:

- A chat picked up from Zendesk is an enterprise ticket when its requester can chat about
  the product, otherwise a personal product ticket. With the switch on and chat settings
  missing, pickup fails instead (see [Chat](zendesk.md#chat)).
- Losing chat tags the user's active Zendesk chats `chat-access-revoked`. Chats started
  after the change and chats already tagged are skipped. Nothing is tagged while the switch
  is off.

Revocation triggers:

- Leaving the company: removal from the company or a department group, deletion of their
  group, their group's Django group changed in admin, or their department moving out of
  the company. All of the user's chats are tagged. A user still in the company through
  another group isn't tagged.
- Account deactivation or deletion: all of the user's chats are tagged.
- A contract or coverage change that leaves a product without chat (the contract leaving
  active status or no longer covering today, or a coverage's chat turned off): every active
  member of the company and its departments has that product's chats tagged.
- The daily `revoke_expired_chat` task, for chat coverage that ended in the past week, with
  the same effect; missed runs catch up.
- Archiving a product: every active member of a company whose effective coverage of it
  includes chat, and of its departments, has that product's chats tagged.

Gotchas:

- Product-scoped revocation spares a chat only when its product tag names a single other
  product. Chats with no product tag or several are tagged, because the widget sets the
  tags in the browser.
- Coverage that ended within the past week still counts when someone leaves or is closed,
  so a departure between expiry and the daily job is still tagged.
- Users who are already inactive aren't tagged again by later changes.
- Code that adds a new way to lose chat must call `queue_chat_revocation`
  (`groups/membership.py`) or `revoke_company_chat_tickets` (`customercare/tasks.py`).

## On the site

- On a covered product's page, users get links to the shared form, the product's top-level
  `getting-started` topic (when it exists), and their company page.
- Users with coverage for any product get a link to their company's support section on the
  home page, the product list, and other product pages; covered products appear in the
  Ask a Question product picker.
- Users in exactly one company get a link to that section in the user menu, and so do
  department pages within their company. It doesn't depend on coverage, so it stays after
  a contract expires.

### Company support section

| Viewer | Sees |
| --- | --- |
| Company or department member | Covered products with access to the shared form (not in read-only mode), ticket history link |
| Company leader, root leader, superuser, non-member staff | Covered products without the form, ticket history link |
| Anyone else | Nothing |

Without coverage it says the company has no active support coverage. It never shows
contract, Zendesk, or chat details.

## Ticket history

New enterprise tickets, including chats picked up with chat coverage, belong to the
contract's company. Product tickets have no owning group; older tickets keep the group they
were saved with.

Behavior:

- Visibility follows the owning group's place in the tree, not coverage, so history stays
  after a contract expires.
- The requester, staff, and superusers always see a ticket. For a company or department
  ticket, so do members of that group or any group below it, its leaders, and root leaders;
  a department's tickets aren't shown to the rest of the company.
- Only the requester can reply, and never to a chat.
- Companies list their sent tickets for viewers who can see them; departments list tickets
  only when they own sent ones.

## Adding people

Operators add people to a company. Intake (`kitsune.groups.onboarding.invite_enterprise_user`)
prepares the SUMO account and records the invitation, then provisioning runs in the same
request ([Zendesk provisioning](#zendesk-provisioning)). It needs the operator permissions
and root settings of company setup, is refused in read-only mode, and sends no mail and
activates nothing itself; successful provisioning queues the welcome email. Unaccepted
invitations, with status and failure reason, are listed only to operators, who can resend
them. Sign-in behavior is in [Users](users.md#enterprise-account-preparation).

Behavior:

- Each request takes one valid email (matched ignoring case and surrounding whitespace) and
  both first and last names.
- New accounts are inactive, have unusable passwords, keep their email private, and have no
  Mozilla account.
- Existing active, regular accounts linked to a Mozilla account are reused, keeping their
  names, identity, subscriptions, and support history, unless they are staff or superusers.
- Hidden system accounts, legacy accounts without a Mozilla account, inactive accounts the
  invitation didn't prepare, duplicate emails, and accounts in another company (refused
  without naming it) need an administrator. Accounts are never merged and memberships never
  moved.
- One unfinished invitation per email, ignoring case. Repeating intake for the same company
  keeps the prepared account and invitation; another company's unfinished invitation is
  refused.
- Adding someone already `ready` changes nothing and points to resending; `pending` and
  `failed` invitations are provisioned again.
- An unlinked, invitation-created account that has been activated, given a usable password,
  migrated to Mozilla accounts, or used to sign in is refused.
- A failed intake leaves nothing behind, so adding the person again is safe.

Settings: `ENTERPRISE_INVITATION_MAX_AGE` (first-login link lifetime in seconds, default
seven days) and `ENTERPRISE_ONBOARDING_LANDING_PATH` (optional local path to land on after
first login; the company page when empty). Intake refuses invalid values.

## Welcome email and first login

The welcome email, in the recipient's locale, names the company and lists what the account
can do: open tickets for the covered products (omitted without coverage), see tickets
opened by others at the company, and chat with an agent (only when one of those coverages
includes chat and the `zendesk-chat` switch and chat settings are in place).

Behavior:

- The email is saved as a post-office `Email` and sent after commit; if publishing fails,
  the scheduled queue run delivers it.
- New accounts get a personal first-login link that starts a fresh
  `ENTERPRISE_INVITATION_MAX_AGE` window; the email expires with it. Existing accounts are
  already accepted, so their link just starts Mozilla sign-in and continues to the landing
  page.
- Resending a `ready` invitation (`kitsune.groups.invitations.resend_enterprise_invitation`)
  revalidates the account and company and replaces the link. Earlier links stop working; an
  unsent earlier email is expired, and one already in flight may still arrive with a dead
  link.
- The link opens the `groups.invitation` page. Signing in there with the invited email
  activates the account and lands on `ENTERPRISE_ONBOARDING_LANDING_PATH` or, when blank,
  the company page in the account's locale. See [Users](users.md#invited-first-login).

Gotchas:

- The link is a credential that appears only in the email: keep it out of logs and
  analytics.
- Accepting requires the person to still be a company member, so removing them first
  breaks the link.

## Zendesk provisioning

Adding a person calls `kitsune.groups.provisioning.provision_enterprise_invitation` in the
request to create or link the company's Zendesk organization (once per company), the user,
and the organization membership. Zendesk-side rules are in
[Zendesk provisioning](zendesk.md#enterprise-provisioning).

Behavior:

- It refuses read-only mode, never recreates missing local resources, and leaves accepted
  invitations unchanged.
- Records are revalidated after the Zendesk calls, so a change in flight discards the result.
- Conflicting identities, or Zendesk IDs owned by another SUMO profile, need an
  administrator and are reported only as safe codes.
- Success saves the Zendesk IDs, adds the Zendesk and SUMO company memberships, and queues
  the welcome email in one transaction. Invitations for accounts created by intake become
  `ready`; those for existing accounts become `accepted`. Root membership, leadership, and
  account activation are never granted.
- Expected provider failures mark the invitation `failed` with the step and a safe error
  code. Unexpected failures raise and roll back local changes.
- Staff retry by resending, which reruns the whole sequence with the saved IDs, the
  organization UUID, and the invited email, reconciling earlier partial remote work. A rerun
  never sends a second welcome, but queues one for a `ready` invitation that has none.
  Nothing retries automatically.

## Membership mirroring

SUMO membership is the source of truth. Every company membership change made through group
management, admin, or the ORM's many-to-many managers (including group creation, deletion,
reassignment, moves, and inactive-member cleanup) queues
`kitsune.groups.tasks.sync_enterprise_zendesk_membership(user_id)` after commit for each
affected user; rolled-back changes queue nothing. The task reconciles current state, not the
triggering change.

Behavior:

- For a member, it ensures the company's Zendesk organization and an eligible end user,
  removes memberships in other SUMO-linked organizations (including those of deleted
  mappings, passed as `removed_organization_ids`), then ensures the company membership.
- So a member is in at most one SUMO company organization, and organizations SUMO never
  linked (including agent-created ones) are never touched. Leaving the last company removes
  the SUMO-linked memberships.
- If more than one company matches, sync logs `company_conflict` and stops before calling
  Zendesk until an administrator fixes the memberships.
- Deleting a user with a saved Zendesk ID queues
  `kitsune.groups.tasks.remove_stale_zendesk_memberships(user_id, zendesk_user_id, organization_ids)`
  after commit, whatever their membership, with every nonempty SUMO-linked organization ID
  captured before the cascade. Removal paths and identity changes found during a sync queue
  the same cleanup, which needs no surviving user, profile, or mapping and never removes a
  surviving account's current company organization.
- Tasks skip read-only mode and retry provider failures and local-state changes for about
  25 minutes, so Zendesk rate limiting doesn't drop a removal. Unexpected errors aren't
  retried.

Gotchas:

- Old memberships are removed before the new one is added, so a new join doesn't move
  former-company tickets. When the target membership already exists, removing another
  membership may move the member's open tickets into the company's organization. Verify
  both cases in a Zendesk sandbox.
- Failures are logged with only the error class and HTTP status, because provider messages
  can contain email addresses.

Recovery:

- A removal that still fails after its retries leaves the former member in the company's
  Zendesk organization, with the warning
  `Zendesk unavailable for user <user ID>: <error class> <HTTP status>` for each failure.
- Existing account: requeue `sync_enterprise_zendesk_membership(user_id)` with the failed
  task's `removed_organization_ids`, if any. Deleted account: requeue
  `remove_stale_zendesk_memberships` with the failed task's arguments. If they're gone,
  remove the membership in Zendesk Admin Center.
- To reconcile all current members after a deployment or configuration change, run
  `docker compose run --rm web ./manage.py sync_enterprise_zendesk_memberships`. It syncs
  each member once, including department-only members, sequentially without queuing jobs,
  reports each failure, continues, and exits unsuccessfully if any failed; fix and rerun.
  Read-only mode refuses it. It skips root-only and former members, so departures that were
  never synced aren't cleaned up; without a root it reports zero members.

## Testing

- `kitsune/groups/tests/test_zendesk_membership.py`: synchronization, identity conflicts,
  provider failures.
- `kitsune/groups/tests/test_zendesk_membership_changes.py`: membership, hierarchy, and
  admin changes.
- `kitsune/groups/tests/test_deleted_user_membership.py`: real commit and rollback,
  identities captured before cascades, cleanup safeguards.
- `kitsune/groups/tests/test_sync_enterprise_zendesk_memberships.py`: the reconciliation
  command.
- `kitsune/customercare/tests/test_signals.py`: chat revocation triggers.
- `kitsune/products/tests/test_support_routing.py`: effective coverage and chat rules.
