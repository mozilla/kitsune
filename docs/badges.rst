======
Badges
======

Badges in kitsune are based off of `Django Badger <https://github.com/mozilla/django-badger>`_,

As of Q3 2018, kitsune issues four badges per calendar year:

#. KB Badge
#. L10n Badge
#. Support Forum Badge
#. Army of Awesome Badge

A list of active badges can be seen at `https://support.mozilla.org/badges/ <https://support.mozilla.org/en-US/badges/>`_.

KB Badge & L10n Badge
---------------------

The KB Badge is awarded after a user has reached 10 approved English edits on knowledge base articles.

The L10n Badge is awarded after a user has reached 10 approved translation edits on knowledge base articles.

Logic for both badges can be found in ``kitsune.wiki.badges``.

The number of edits needed is configurable in ``settings.BADGE_LIMIT_L10N_KB``.

Support Forum Badge
-------------------

The Support Forum Badge is awarded after a user has reached 30 support forum replies.

Logic for awarding this badge can be found in ``kitsune.questions.badges``.

The number of replies needed is configurable in ``settings.BADGE_LIMIT_SUPPORT_FORUM``.

Army of Awesome Badge
---------------------

The Army of Awesome Badge is awarded when a user has tweeted 50 Army of Awesome replies.

Logic for awarding this badge can be found in ``kitsune.customercare.badges``.

Logic for tweet collection (via the Twitter API) can be found in ``kitsune.customercare`` management commands.

The number of replies needed is configurable in ``settings.BADGE_LIMIT_ARMY_OF_AWESOME``.

Badge Creation
==============

Badges are either created manually through the Django Admin *or* created automatically via ``get_or_create_badge`` in ``kitsune.kbadge.utils``.

Creation through the Django Admin is the usual and preferred method.
