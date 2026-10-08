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
identity. It is service-only and does not deliver invitations, activate accounts,
or grant company membership.

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

See [Enterprise account preparation](groups.md#enterprise-account-preparation)
for operator permissions, required information, eligibility, configuration, and
repeat-intake behavior, and [Enterprise company membership](groups.md#enterprise-company-membership)
for membership boundaries.
