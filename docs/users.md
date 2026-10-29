---
subtitle: Mozilla Accounts
title: Users
---

Kitsune uses Mozilla accounts for authentication:
<https://support.mozilla.org/kb/firefox-accounts-mozilla-support-faq>

## Account managers

`User.objects` excludes users whose profiles are marked as system accounts;
`User.all_users` is Django's original unfiltered manager, for operations that must include
them.

`UserConfig.ready()` installs the filtered manager and group-access monitoring once per
`User` model. Django can call it again when rebuilding the app registry (for example in
tests that override `INSTALLED_APPS`), so reinitializing must keep the original unfiltered
manager and must not wrap monitoring twice.

## Enterprise account preparation

Adding a person to an enterprise company can create an inactive SUMO account before their
first Mozilla sign-in, or reuse an eligible account without changing its identity. It also
provisions Zendesk and grants company membership; the account stays inactive until first
login. See [Adding people](enterprise-support.md#adding-people).

- Ordinary Mozilla sign-in can't claim an unclaimed, invitation-created account by matching
  its email, and doesn't apply Mozilla profile updates to it, so a prepared account isn't
  ready to sign in until it's claimed through the invitation.
- Existing Mozilla account associations take precedence over email matching. Legacy SUMO
  accounts aren't linked to Mozilla accounts automatically, and hidden system accounts count
  when detecting identity and email conflicts. Conflicts need an administrator, never an
  automatic merge.
- Concurrent sign-up and preparation for one email don't create duplicate identities. If
  preparation finishes first, ordinary sign-in refuses the unclaimed account; if sign-up
  finishes first, preparation checks the account's eligibility before reusing it.
- Mozilla account refreshes keep locally saved deactivation, password, and first/last-name
  changes. An account made hidden before a pending refresh resumes is refused, not updated.

## Invited first login

- The invitation token is tied to the OAuth state of the sign-in it started, so the callback
  claims only that invitation; the token is never sent to Mozilla.
- The verified Mozilla email must match the invitation, and its UID must not belong to
  another profile. The verified identity decides: a different signed-in SUMO session is
  replaced.
- The prepared account must still be inactive, unused, and without a Mozilla identity.
  Zendesk is bound before local activation, and acceptance commits with the profile update,
  so a rollback can safely replay the same binding.
- Captured names and the unusable password are kept. An empty display name is set to the
  captured full name (truncated to the limit), so profile sync keeps the name provisioned in
  Zendesk. Later sign-ins need no invitation.
- Validation and provider failures return to the invitation page without accepting.
  Cancelling Mozilla sign-in returns there without an error, ready to retry.
- Profile and email-identity sync tasks are queued after commit; a queueing failure is
  logged without failing the sign-in.

Company membership rules: [Hierarchy and membership](enterprise-support.md#hierarchy-and-membership).
