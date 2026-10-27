# Groups System

Kitsune's groups system provides hierarchical organization for users with configurable visibility, isolation, and leadership delegation.

## Overview

Groups enable organizing users into hierarchical structures for:
- **Content Access Control**: Restrict wiki articles, questions, and other content to specific groups
- **Moderation Delegation**: Assign leaders who manage group members and content
- **Hierarchical Organization**: Support nested group structures with parent-child relationships
- **Isolated Workspaces**: Prevent sibling groups from discovering each other

## Architecture

### Hierarchy Structure

Groups use django-treebeard's Materialized Path (MP_Node) implementation:
- **Unlimited depth**: Support for deeply nested structures (recommended max: 3-4 levels)
- **Single parent**: Each group belongs to exactly one parent (no multiple inheritance)
- **Efficient queries**: Path-based lookups for ancestors and descendants

**Example Hierarchy:**
```
Organization (root)
├── GroupA
│   ├── SubgroupX
│   └── SubgroupY
└── GroupB
    └── SubgroupZ
```

### Key Models

**TreeModelBase** (`kitsune.groups.models.TreeModelBase`)
- Abstract base combining `MP_Node` (tree operations) + `ModelBase` (Kitsune methods)
- Provides: `get_parent()`, `get_children()`, `add_child()`, `get_ancestors()`, `get_descendants()`, `get_root()`

**GroupProfile** (`kitsune.groups.models.GroupProfile`)
- Profile extending Django's `Group` with hierarchy support
- Fields: `slug`, `group` (ForeignKey), `leaders` (M2M), `information`, `avatar`, `visibility`, `isolation_enabled`, `visible_to_groups`
- Methods: `can_moderate_group()`, `can_edit()`, `can_delete_subgroup()`, `can_view()`, `get_visible_children()`

## Visibility Levels

Groups have three visibility levels that control discovery and access.

### PUBLIC
- **Who can see**: Everyone (anonymous and authenticated users)
- **Isolation**: None - all PUBLIC groups are globally visible
- **Behavior**: No restrictions on visibility

### PRIVATE
- **Who can see**: Depends on `isolation_enabled` setting (default: True)
- **With isolation enabled**: Members/moderators see only their hierarchy (sibling isolation)
- **With isolation disabled**: Members see entire tree
- **Behavior**: Restricts visibility to members and moderators within the hierarchy

### MODERATED
- **Functionality**: Identical to PRIVATE
- **Additional feature**: `visible_to_groups` for cross-hierarchy view access
- **Behavior**: Same as PRIVATE, plus allows specific external groups to view (but not edit)

## Isolation

### Isolation Setting

Both PRIVATE and MODERATED groups have an `isolation_enabled` field (default: `True`). PUBLIC groups do not have isolation as it doesn't make sense for publicly visible content.

**With Isolation Enabled (default):**
```
Root (member: Alice, Bob; moderator: Mike)
├── SubA (member: Alice, Charlie)
└── SubB (member: Bob)

Mike (root moderator):     Sees Root, SubA, SubB (entire tree)
Alice (root member):       Sees Root, SubA, SubB (entire tree, view-only)
Bob (root member):         Sees Root, SubA, SubB (entire tree, view-only)
Charlie (node member):     Sees Root, SubA ONLY (sibling isolation - no SubB)
```

**Key Rules:**
- **Root moderators**: View + edit entire tree
- **Root members**: View entire tree (read-only)
- **Node members** (not root members): View ancestors + own subtree (sibling isolation)
- **Ancestors always visible**: Everyone in a hierarchy can see ancestor groups

### Why Isolation Matters

Sibling isolation prevents cross-group information leakage:
```
Organization (PRIVATE, isolation=True)
├── GroupA (members: Alice, Bob)
└── GroupB (members: Charlie, Dana)

- Alice and Bob cannot discover GroupB exists
- Charlie and Dana cannot discover GroupA exists
- Prevents users from discovering sibling groups they are not members of
```

## Leadership and Moderation

### Moderation Hierarchy

**Root Moderators (full tree access):**
- Leaders of root group can moderate entire tree
- Can add/remove members anywhere
- Can edit all group settings
- **Only ones who can delete subgroups**

**Non-Root Moderators (limited to their group):**
- Can moderate ONLY their specific group (not descendants)
- Can add/remove members to their group
- Can edit their group's settings
- **Cannot delete subgroups**

**Example:**
```
Root (moderator: Mike)
├── SubA (moderator: Alice)
│   └── SubSubA (no moderator)
└── SubB (no moderator)

Mike can:
- Moderate Root, SubA, SubSubA, SubB
- Edit all groups
- Delete any subgroup

Alice can:
- Moderate SubA ONLY
- Edit SubA ONLY
- NOT manage SubSubA (her descendant)
- NOT delete subgroups
```

### Moderation Inheritance

If a group has no assigned moderators, moderation **inherits from ROOT only** (not parent):

```
Root (moderator: Mike)
└── SubA (moderator: Alice)
    └── SubSubA (no moderator)
        └── SubSubSubA (no moderator)

SubSubA: Moderated by Mike (root), NOT Alice (parent)
SubSubSubA: Moderated by Mike (root), NOT Alice (grandparent)
```

**Why skip parent?** This ensures clear chain of command - only root moderators or explicitly assigned group moderators can manage groups.

### Root Must Have Moderators

**Validation**: Root groups must have at least one moderator assigned. This ensures there's always someone who can manage the entire tree.

## Visibility Inheritance

**Strict Inheritance Rule**: Children automatically inherit parent's visibility.

- Cannot mix visibility levels in a tree (e.g., PUBLIC parent with PRIVATE child)
- Enforced by `save()` method - children automatically match parent's visibility
- Changing root visibility propagates to all descendants

## Enterprise company setup

The enterprise root's group page has an **Enterprise onboarding** card.
**Create company** creates a direct child of that root. Each company's **Support
settings** can turn live chat on or off and link an existing Zendesk organization,
but cannot rename the company. These actions are available only for the configured
enterprise root and its direct company children, not departments or other
hierarchies. Existing username-based member and leader controls remain available,
subject to the company-membership boundary below.

Operators must be active Django staff who either lead the enterprise root or are
superusers. Company leadership alone does not grant onboarding access. Creating
a company does not make the operator a member or leader of it.

Deployment prerequisites:

- `ENTERPRISE_GROUP_SLUG` (default `firefox-enterprise`) identifies the depth-1
  enterprise root group. The root must have PRIVATE or MODERATED visibility and
  sibling isolation enabled. Company setup, invitations, and enterprise tickets do not
  depend on a product support configuration; ticket support comes from
  [contracts](#enterprise-support-contracts).
- Optional live chat requires exactly one nonarchived product whose slug matches
  `ENTERPRISE_GROUP_SLUG`, with an active support configuration that has a Zendesk
  configuration and does not require a product subscription. It also requires the
  `zendesk-chat` switch, `ZENDESK_CHAT_WIDGET_KEY`, `ZENDESK_CHAT_SIGNING_KEY_ID`, and
  `ZENDESK_CHAT_SIGNING_SECRET`. The form does not change these deployment settings.

Live chat is the only company setting stored as a support organization. Turning it on
creates or updates the company's support organization on that product configuration
with live chat included. Turning it off clears live chat on the company's existing
enterprise support organizations and never creates one. Invitations never create
support organizations.

Company names and generated URL slugs must be available; collisions are rejected
without adding a suffix. New companies inherit the root's visibility. Updating
support settings preserves the company's identity and support organizations for
other products. Neither action changes membership or leadership.

An optional existing Zendesk organization ID is verified remotely before linking.
A Zendesk organization can belong to only one company, and a saved link cannot be
reassigned. Equivalent spellings of the same numeric ID retain the existing link.
Names are never used to adopt a remote organization. Leaving the ID blank records
only local support settings; it does not create a remote organization or user.

For company creation and support settings, remote verification completes before
acquiring hierarchy or company-row locks. The locked mutation rechecks operator
permissions, company scope, the live chat configuration when chat is on, and link
ownership before saving. An unchanged canonical organization link does not require a
provider call.

Missing prerequisites and conflicts leave the operation unchanged and display a
form error. Read-only mode refuses both mutations. Department groups and companies
outside the configured root cannot be targeted.

## Enterprise support contracts

Staff record company agreements in Django admin under **Products > Support
contracts**. A contract has a name, a status (active, suspended, or cancelled), and
start and end dates, both inclusive in the site time zone. Each coverage names a product,
its Zendesk form configuration, the Zendesk product value, and whether chat is included.
A bundle is several coverages on one contract.

- The company must be a direct child of the enterprise root and cannot change later.
- A contract needs at least one coverage and lists each product once. In admin, a saved
  coverage's product cannot be changed; its Zendesk configuration and product value can.
- Active and suspended contracts of one company cannot cover the same product in
  overlapping periods. Cancelled contracts never block.
- Contracts and coverages cannot be deleted. Cancel a contract to retire it; to fix a
  mistake, cancel it and enter a new one.
- A company with contracts, in any status, cannot be deleted, moved from directly under
  the root, or given a different Django group in admin.

Saving a contract creates the company's local Zendesk organization identity without
contacting Zendesk.

A user has effective coverage for a product when an active contract of their company
covers it and today falls within the contract's dates. Membership in one of the
company's departments counts; enterprise-root-only membership, leadership, and staff
status do not. Inactive users, members of more than one company, archived products, and
products with more than one effective coverage get no enterprise support. Coverage does
not require a product support configuration, and the product's subscription requirement
does not apply to enterprise tickets.

Effective coverage selects the enterprise form at the shared product support URL,
`/questions/new/<product>/form`, ahead of any product ticket; covered users get no
personal-ticket form for that product. A product forum the user is authorized for stays
available as an explicit alternative. Product pages and the company page present the
enterprise option; see [Enterprise support on the site](#enterprise-support-on-the-site).

Support organizations only carry live chat access; adding or removing one never changes
who gets forum or ticket support. Firefox Enterprise support is contracts-only, with no
individually purchased product. At the cut-off, make the Firefox Enterprise product
support configuration forum-only so its old Zendesk form is never offered as product
support. This also ends organization-based live chat for it.

## Enterprise support on the site

### Product pages

On the page of a product the user has effective coverage for, a **Get help** section
links to **Contact support** (the shared form), **Get started** (the product's
top-level `getting-started` topic, when it exists), and **Manage your account** (the
company page). Users with coverage for any product see a **Your company’s support**
banner on the home page, the product list, and other product pages, linking to the
company page's **Your support** section. Analytics events from these links do not
include the company slug. Covered products also appear in the Ask a Question product
picker.

### Company page

Enterprise company pages have a **Your support** section:

- Members of the company, directly or through a department, see each product with
  effective coverage, covering all of its support topics, with a **Contact support**
  button that opens the shared form.
- Company leaders, enterprise-root leaders, superusers, and staff who are not members
  see the same list without buttons.
- A company without effective coverage shows that it has no active support coverage.
- Viewers who can see the company's tickets get a **View ticket history** link.
- Nobody else sees the section. It shows no contract, Zendesk, or chat details.

Users who belong to exactly one company have **My support** in the user menu, linking to
that section. It does not depend on coverage, so it remains after a contract expires.
Department pages link members of their company to it with **Your company’s support**.

### Ticket history

New enterprise tickets are owned by the contract's company; product tickets have no
owning group, and live chat tickets are owned by the group of the organization that
granted the chat. Older tickets keep the group they were saved with. Visibility follows
the owning group's place in the enterprise tree, not coverage, so history stays
available after a contract expires:

- The owner always sees the ticket. Staff and superusers see every ticket.
- When the owning group is an enterprise company or department, members of that group
  or of any group below it, that group's leaders, and enterprise-root leaders also see
  it. A department's tickets are not shown to the rest of its company.
- Tickets owned by a group outside the enterprise tree are visible only to their owner.
- Only the owner can reply.

Companies have a **Tickets** tab, listing their sent tickets, for viewers who can see
them. Departments have one only when they own sent tickets. Groups outside the
enterprise tree have no ticket list.

## Enterprise account preparation

Staff add people with **Add person** on a company's page. It prepares the SUMO
account, records the invitation, and provisions it in the same request (see below).
It requires the same operator permissions and enterprise root settings as company
setup and is unavailable in read-only mode.

The preparation step itself (`kitsune.groups.onboarding.invite_enterprise_user`)
only creates or reuses the account and records the invitation. Prepared accounts are
not ready for ordinary sign-in; they are claimed through the invitation link.

Below the member list, the company page lists invitations that are not accepted
yet, with their status, the reason for a failure, and a **Resend** button. Accepted
people appear in the member list instead. Only onboarding staff see the form and
invitations.

### Required information and account eligibility

- Each request accepts one valid email address and requires both first and last
  names. Email matching ignores case and surrounding whitespace. Names are trimmed
  but retain Unicode, case, and internal spacing.
- New accounts are inactive, have unusable passwords, keep their email private,
  and are not linked to a Mozilla account. Supplied names are saved only on new
  accounts and are not copied into the public profile display name.
- Existing active, regular accounts linked to a Mozilla account can be reused,
  provided they are neither staff nor superusers. Their names, identity,
  subscriptions, and support history are preserved.
- Hidden system accounts, legacy accounts not linked to a Mozilla account,
  inactive accounts not prepared by this invitation, and case-insensitive duplicate
  email addresses require administrator resolution. Accounts that belong to another
  company, directly or through one of its departments, are refused without naming
  that company. Intake does not merge accounts, move memberships, or resolve
  conflicts automatically.

### Repeating intake and configuration requirements

Only one unfinished invitation is allowed per email address, ignoring case.
Repeating intake for the same company preserves the prepared account and invitation
state; an unfinished invitation to another company is refused. If an accepted
invitation's user still belongs to that company, the accepted record is reused.
An eligible former member can receive a new invitation record without deleting
accepted history.

Adding a person who is already invited and `ready` leaves their invitation and
link unchanged and points staff to **Resend**; pending or failed invitations are
provisioned again. Provisioning checks this against the invitation's current state
under the account-email lock, so a double-submitted Add person or Resend does not
redo setup.

Repeated intake refuses an unlinked, invitation-created account if it has been
activated, given a usable password, migrated to Mozilla accounts, or used to sign
in.

Intake and provisioning do not depend on a product support configuration. The welcome
email reads the Firefox Enterprise configuration only to decide whether to include its
live chat line. A new intake creates the company's local Zendesk organization mapping
if it is missing. Missing prepared accounts or mappings are not recreated for an
existing invitation. Failed intake leaves no partial account preparation.

Intake also validates these deployment settings:

- `ENTERPRISE_INVITATION_MAX_AGE` is a duration in seconds, defaulting to seven days
  (`604800`). It must be a positive integer.
- `ENTERPRISE_ONBOARDING_LANDING_PATH` may be empty. When set, it must be a local
  path starting with a single slash, not a full URL, and contain neither backslashes
  nor control characters.

Intake does not send mail or activate accounts. Successful remote provisioning adds
company membership and queues the welcome email described below.

## Enterprise Zendesk provisioning

**Add person** calls
`kitsune.groups.provisioning.provision_enterprise_invitation(actor=..., invitation=...)`
in the request to create or link the Zendesk organization, user, and organization
membership. The organization is created once per company; later people only get a
user and membership.

Provisioning rechecks operator permissions, the prepared account, the company's
Zendesk organization mapping, and company membership rules. It refuses
read-only mode, never recreates missing local resources, and leaves accepted
invitations unchanged.

Before contacting Zendesk, provisioning commits the company's local organization
mapping and stable UUID, so retries reuse the same remote create-or-update key.
Zendesk requests run while only the account-email lock is held, never while
hierarchy or row locks are held. Afterwards provisioning locks and revalidates the
records before saving. Results are discarded if the company, account, or mapping
changed in flight, except for links matching what this run resolved. Conflicting
identities, or Zendesk IDs owned by another SUMO profile, need administrator resolution.

### Membership mirroring

Company membership changes queue
`kitsune.groups.tasks.sync_enterprise_zendesk_membership(user_id)` after commit:

- **Add person**, group management, admin, and ORM additions/removals/clears.
- Inactive-member cleanup, group or `GroupProfile` deletion, and subtree moves into, out of,
  or between companies. Deletion still reconciles members of shared groups whose
  other profiles survive.
- `GroupProfile` creation for groups with existing members and admin group reassignment, including
  both former and new members.

Removal paths capture former company organization IDs before mappings disappear.
When a saved remote user ID exists, they also queue captured-identity cleanup. It
survives subsequent company or user deletion; rolled-back mutations publish neither task.

Direct company membership and membership in descendant departments count;
enterprise-root-only membership and leadership do not. The task reconciles current
state rather than replaying the triggering change. While a user belongs to a
company, it ensures the company's Zendesk organization and eligible end user,
removes memberships in other Zendesk organizations linked to SUMO companies or
captured from deleted company mappings, and then ensures the company's membership.
Members therefore belong to at most one SUMO company organization; unrelated organizations
are untouched. Removing old SUMO-company memberships before creating the target
membership avoids rehoming former-company tickets into the new company on new joins.
If the target membership already exists, removing another SUMO-company membership
may move the member's open tickets into the company's organization under Zendesk's
behavior. Verify both cases in a Zendesk sandbox.

If more than one company matches, synchronization logs `company_conflict` and stops
before provider calls; an administrator must correct the memberships. Deleted-account
cleanup needs no target company and can still remove captured memberships.

Leaving the last company removes SUMO-linked memberships. Deleted mappings remain
removal targets through `removed_organization_ids`, including former companies moved
outside the enterprise tree and their departments. Joining another company before
the worker runs does not preserve old grants; synchronization preserves the current target.

Deleting any user with a saved Zendesk ID captures that ID and every nonempty
SUMO-linked organization ID before the user, profile, and membership rows cascade.
After commit, it queues
`kitsune.groups.tasks.remove_stale_zendesk_memberships(user_id, zendesk_user_id, organization_ids)`.
This applies without current company membership, including root-only members, leaders,
and ambiguous memberships. Removing membership and then deleting the account cannot
strand a grant: this task needs no surviving user, profile, or company mapping.

The deletion signal skips missing profiles/IDs and conflicting local ownership.
Cleanup rechecks ownership, rejects elevated/shared remote roles, and logs conflicts
using only user IDs and safe codes. Removal permits email, Mozilla identity, and
active/suspended-status drift; these do not justify retaining old company access.

Synchronization commits the organization mapping/UUID before provider calls and
revalidates local state under short locks afterward. Safely validated links survive
membership changes so retries can remove stale grants. Remote calls hold the account-email
lock, never hierarchy or row locks. Cleanup for a deleted account runs without the
account-email lock and relies on the local-ownership check.

If the account or mapping disappears or is replaced during setup, queue cleanup after
commit for that attempt's resolved remote user/organization pair. Do the same when an
email/FxA identity change or profile replacement invalidates the saved setup identity,
even if company membership is unchanged. Never persist an invalidated link.
Cleanup preserves a surviving account's current company organization only while its
profile still owns the captured Zendesk user ID. Otherwise it removes the stale identity's
captured memberships. It neither removes unrelated organizations nor recreates memberships;
no matching remote memberships is a successful no-op.

Invitation provisioning uses this cleanup when local revalidation fails after remote
identities were resolved. Cleanup is queued outside the failed local transaction so
rolling back local writes cannot strand an already-created remote membership. The
original validation error is preserved; no local invitation access is granted.

Background membership tasks skip read-only mode and retry expected provider failures
and local-state changes up to six times, with jittered exponential backoff from 30
seconds capped at ten minutes (up to about 25 minutes in total), so Zendesk rate
limiting does not drop a removal.
Provider failures are logged and retried as only the error class and HTTP status,
because provider messages can contain email addresses. Unexpected programming errors
are not retried. Permanent identity conflicts are logged and require administrator
correction.

A removal that still fails after its retries leaves the former member in the company's
Zendesk organization. Each provider failure logs the warning `Zendesk unavailable for
user <user ID>: <error class> <HTTP status>`. For an existing account, requeue
`sync_enterprise_zendesk_membership(user_id)`, passing the failed task's
`removed_organization_ids` if it had any. For a deleted account, requeue
`remove_stale_zendesk_memberships` with the failed task's arguments: user ID, Zendesk
user ID, and organization IDs. If those arguments are no longer available (the warning
carries only the user ID and the error class and status), remove the membership in
Zendesk Admin Center.

To reconcile existing company members after deployment or configuration changes,
run:

```sh
docker compose run --rm web ./manage.py sync_enterprise_zendesk_memberships
```

The command synchronizes each current company member once, including department-only
members, sequentially in the command process. Each failed member gets one line with
the user ID and either a safe failure code, `ZendeskUnavailable` with the provider
error class and HTTP status, or the class name of a local-state change or database
error. The run continues with the next member, prints a completion summary, and exits
unsuccessfully if any member failed. Resolve those failures and rerun the command; it
reuses the same synchronization logic as membership events without queuing a batch of
jobs. Read-only mode refuses the run. It excludes root-only members and unrelated
users; without an enterprise root it reports zero members. It does not scan former
members.

The contract-support cutover is a hard cut-off with no active Firefox Enterprise
users. Firefox Enterprise ticket support and chat are contracts-only; at the cut-off,
edit the Firefox Enterprise product support configuration in Django admin to make it
forum-only. This is an admin change, not a data migration, and also ends
organization-based chat.

After deployment, keep admissions paused and run `sync_enterprise_zendesk_memberships`
before reopening. Resolve any failures and rerun until the command completes
successfully, verify ticket delivery, then reopen admissions. The command does not
clean up pre-deploy departures. Audit earlier invitees who have left, using surviving
invitation records and validated saved user and organization links to remove old
access. Invitations cannot recover historical Zendesk IDs after accounts or company
mappings are deleted, so they cannot identify every former membership.

### Status and recovery

- Success saves the Zendesk IDs and adds both the Zendesk membership and membership
  in the company's SUMO group, then queues the welcome email in the same transaction.
  Invitations for accounts created by intake become `ready`; invitations for
  existing accounts become `accepted`. It does not add root membership or
  leadership, or activate accounts.
- Expected provider failures return `failed` with the failed step and a safe error
  code. Unexpected failures raise and roll back local changes.
- Staff retry with the **Resend** button, which reruns the full sequence using saved
  IDs, the organization UUID, and the invited email, so earlier partial remote work
  is reconciled. A rerun never sends a second welcome, but queues one for a `ready`
  invitation that has none. Invitation provisioning is not retried automatically.

See [Zendesk provisioning](zendesk.md#enterprise-provisioning) for provider
permissions and identity rules.

## Enterprise welcome email and first login

The welcome email names the company and lists what the account can do, in the
recipient's locale:

- Open support tickets for the products the company has effective coverage for, by
  name. Without coverage this item is omitted.
- See the support tickets opened by others at the company.
- Chat live with a support agent, only when the company's support organization has
  live chat and live chat is deployed as described in
  [company setup](#enterprise-company-setup).

It is built as a post-office `Email` row, linked from the invitation, and sent after
commit; if publishing fails, the scheduled queue run delivers it.

- Accounts created by intake get a personal link to start first login. Queuing it
  starts a fresh `ENTERPRISE_INVITATION_MAX_AGE` window, and the email itself
  expires with the link.
- Existing accounts are already accepted, so their email carries no token. Its link
  starts Mozilla sign-in and then continues to the landing page described below, since
  a signed-out visitor cannot see the private company page.

The link is a credential; it only appears in the email, so keep it out of logs and
analytics. For a `ready` invitation, **Resend** calls
`kitsune.groups.invitations.resend_enterprise_invitation(actor=..., invitation=...)`
to replace an unused or expired link. It revalidates the account
and company like first login, and invalidates every earlier link. An unsent earlier
email is expired so it is never delivered; one already in flight may still arrive,
but its link no longer works.

Opening the link moves the token into the session and redirects to the
`groups.invitation` page, which shows the company and invited email. Continuing
starts Mozilla sign-in. Signing in with the invited email activates the prepared
account, links its Mozilla and Zendesk identities, consumes the link, and lands on
`ENTERPRISE_ONBOARDING_LANDING_PATH` or, when blank, the company page in the
account's locale.

Acceptance requires the saved account, Zendesk mappings, and company membership, and
never recreates them. See [Users](users.md#invited-first-login) for sign-in rules and
failure handling.

## Enterprise company membership

A user may belong to only one direct company child of `ENTERPRISE_GROUP_SLUG`.
Membership in any descendant counts toward that company. Multiple departments
within the same company are allowed; company/root membership is not added
implicitly. Root operator membership and unrelated hierarchies are unchanged.
Staff and superusers have no exception to the company-membership boundary.

Member and leader controls and Django admin membership changes enforce this
boundary, including membership granted when assigning a group leader. A conflicting
batch of changes is rejected as a whole. Moving groups or changing their associated
Django groups is also refused if it would leave a user in more than one company.
Errors do not disclose the name of another private company.

Existing conflicts are not repaired automatically. Membership removals remain
available so an administrator can resolve them before retrying an addition.
Use the normal group-management paths for membership changes; direct writes to
membership tables bypass these safeguards. A company's or department's Django group must
not also back a group profile outside the enterprise tree: membership added there makes
the user a member of the company.

## Security

### Critical: Always Use `.visible()`

**⚠️ SECURITY WARNING**: Always use `GroupProfile.objects.visible(user)` instead of `.all()` when querying groups. Using `.all()` bypasses visibility and isolation rules, potentially exposing PRIVATE groups to unauthorized users.

- ✅ **SECURE**: `GroupProfile.objects.visible(request.user)` - Respects visibility and isolation
- ❌ **INSECURE**: `GroupProfile.objects.all()` - Bypasses all security, exposes all groups

All views must filter by `.visible()` or explicitly check `can_view()` permissions.

## Cross-Hierarchy View Access

The `visible_to_groups` M2M field allows external groups to have **view-only** access to MODERATED groups. This enables oversight or auditing scenarios where certain groups need to see (but not edit) other groups outside their hierarchy.

**Behavior:**
- External groups can view MODERATED groups without being members
- View-only access (cannot edit or moderate)
- Useful for oversight, auditing, or cross-team visibility

## Testing

Test coverage includes 58 tests in `kitsune/groups/tests/test_models.py`:
- **ModerationHierarchyTests**: Root vs non-root moderator permissions (6 tests)
- **VisibilityWithIsolationTests**: Visibility rules with isolation enabled (4 tests)
- **PublicGroupsNoIsolationTests**: PUBLIC group behavior (2 tests)
- **ModeratedGroupsTests**: MODERATED group behavior and cross-hierarchy access (2 tests)
- **IsolationDisabledTests**: Behavior when isolation is disabled (1 test)
- **SiblingIsolationTests**: Sibling isolation functionality (7 tests)
- **VisibilityEdgeCaseTests**: Edge cases in group visibility (9 tests)
- **GetVisibleChildrenTests**: Visible children filtering (5 tests)
- **LeadershipVisibilityTests**: Leader visibility permissions (6 tests)
- **VisibilityInheritanceTests**: Visibility inheritance rules (2 tests)
- **ModeratedVisibilityTests**: MODERATED group visibility (5 tests)

Membership tests cover the following paths:

- `kitsune/groups/tests/test_zendesk_membership.py`: synchronization, identity conflicts,
  and provider failures.
- `kitsune/groups/tests/test_zendesk_membership_changes.py`: membership, hierarchy,
  and admin changes.
- `kitsune/groups/tests/test_deleted_user_membership.py`: real commit and rollback
  behavior, captured identities surviving cascades, and cleanup safeguards.
- `kitsune/groups/tests/test_sync_enterprise_zendesk_memberships.py`: sequential
  reconciliation, member selection, and failure reporting.

Run tests:
```bash
# All groups tests
docker compose run --rm web python manage.py test kitsune.groups.tests

# Specific test file
docker compose run --rm web python manage.py test kitsune.groups.tests.test_models
```

## Key Behaviors

- **Visibility Inheritance**: Children automatically match parent's visibility level
- **Moderation Scope**: Root moderators manage entire tree; non-root moderators manage only their specific group
- **Moderation Inheritance**: Groups without assigned moderators inherit from root (not parent)
- **Member Visibility**: Root members see entire tree; node members see only their subtree (with sibling isolation)
- **Deletion Rights**: Only root moderators can delete subgroups

## References

- **GitHub Issue**: [#2692 - Nested Groups](https://github.com/mozilla/sumo/issues/2692)
- **django-treebeard**: https://django-treebeard.readthedocs.io/
- **Model**: `kitsune/groups/models.py`
- **Manager**: `kitsune/groups/managers.py`
- **Views**: `kitsune/groups/views.py`
- **Tests**: `kitsune/groups/tests/test_models.py`
