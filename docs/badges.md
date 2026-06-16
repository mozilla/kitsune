---
title: Badges
---

Badges in kitsune are based on modified [Django
Badger](https://github.com/mozilla/django-badger).

Kitsune issues four badges per calendar year:

1.  KB Badge
2.  L10n Badge
3.  Reviewer Badge
4.  Support Forum Badge

The Army of Awesome Badge was also issued annually until 2020
when it was discontinued.

A full list of active badges can be seen at
https://support.mozilla.org/badges/.

# KB Badge & L10n Badge

The KB Badge is awarded after a user has reached 10 approved English
revisions on knowledge base articles.

The L10n Badge is awarded after a user has reached 10 approved
translation revisions on knowledge base articles.

Logic for both badges can be found in `kitsune.wiki.badges`.

The number of revisions needed is configurable in
`settings.BADGE_LIMIT_L10N_KB`.

# Reviewer Badge

The Reviewer Badge is awarded after a user has reached 25 English
revisions reviewed by them on knowledge base articles.

Logic for awarding this badge can be found in `kitsune.wiki.badges`.

The number of reviews needed is configurable in
`settings.BADGE_LIMIT_REVIEWER`.

# Support Forum Badge

The Support Forum Badge is awarded after a user has reached 30 support
forum replies.

Logic for awarding this badge can be found in
`kitsune.questions.badges`.

The number of replies needed is configurable in
`settings.BADGE_LIMIT_SUPPORT_FORUM`.

# Army of Awesome Badge

!!! warning

    This badge is no longer issued/awarded.

The Army of Awesome Badge used to be awarded when a user had tweeted 50 Army of
Awesome replies.

## Badge Creation

Badges are either created manually through the Django Admin *or* created
automatically via `get_or_create_badge` in `kitsune.kbadge.utils`.

Creation through the Django Admin is the usual and preferred method.
