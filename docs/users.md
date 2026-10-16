---
subtitle: Mozilla Accounts
title: Users
---

Kitsune uses Mozilla accounts for authentication:
<https://support.mozilla.org/kb/firefox-accounts-mozilla-support-faq>

## Account managers

`User.objects` excludes users whose profiles are marked as system accounts.
`User.all_users` retains Django's original unfiltered manager for operations that
must include those accounts.

`UserConfig.ready()` installs the filtered manager and group-access monitoring
once per `User` model. Django can call it again when rebuilding the app registry,
including during tests that override `INSTALLED_APPS`. Reinitialization must
preserve the original unfiltered manager and avoid wrapping monitoring again.

## Enterprise account preparation

Enterprise preparation can create an inactive SUMO account before its first
Mozilla sign-in, or reuse an eligible account without changing its existing
identity. Staff do this with **Add person** on the company page, which also
provisions Zendesk and grants company membership; the account stays inactive until
first login.

Ordinary Mozilla sign-in cannot claim an unclaimed, invitation-created account by
matching its email address, and does not apply Mozilla profile updates to that
account. Preparing an account therefore does not make it ready to sign in.

Existing Mozilla account associations still take precedence over email matching.
Legacy SUMO accounts are not automatically linked to Mozilla accounts, and hidden
system accounts are included when detecting identity and email conflicts.
Conflicting identities require administrator resolution rather than an automatic
merge.

Concurrent sign-up and preparation for the same email address do not create
duplicate identities. If preparation finishes first, ordinary sign-in refuses the
unclaimed account. If sign-up finishes first, preparation checks the account's
eligibility before reusing it.

Mozilla account refreshes preserve locally saved deactivation, password, and
first/last-name changes. An account made hidden before a pending refresh resumes
is refused rather than updated.

## Invited first login

The invitation token is tied to the OAuth state of the sign-in it started, so the
callback claims only that invitation; the token is never sent to Mozilla. The
verified Mozilla email must match the invitation and its UID must not belong to
another profile. The verified identity decides: a different signed-in SUMO session
is replaced.

The prepared account must still be inactive, unused, and without a Mozilla
identity. Zendesk is bound before local activation, and acceptance commits together
with the profile update, so a rollback can safely replay the same binding. Captured
names and the unusable password are kept; an empty display name is set to the
captured full name, truncated to the display-name limit, so profile sync keeps the
provisioned Zendesk name. Later sign-ins need no invitation.

Validation and provider failures return to the invitation page without accepting.
Cancelling Mozilla sign-in returns to the invitation without an error, ready to
retry. Profile and email-identity sync tasks are queued after commit; queueing
failures are logged without failing the sign-in.

See [preparation requirements](groups.md#enterprise-account-preparation)
and [membership rules](groups.md#enterprise-company-membership).
