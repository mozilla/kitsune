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
