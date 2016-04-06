============================
Standard Operating Procedure
============================

Site is broken because of bad locale msgstr
===========================================

Occasionally, the localized strings cause the site to break.

For example, this causes the site to break::

    #: kitsune/questions/templates/questions/includes/answer.html:19
    msgid "{num} answers"
    msgstr "{0} antwoorden"

In this example, the `{0}` is wrong.

How to fix it:

* If Kadir is around:

  1. Tell Kadir. He can fix it in Pontoon.
  2. Once it's fixed, push to production. This will pick up the
     new strings.

* If someone with commit access to the
  `locales Git repo <https://github.com/mozilla-l10n/sumo-l10n>`_ is around:

  1. Tell that person. She/he can fix it in Git.
  2. Once it's fixed, push to production. This will pick up the
     new strings.
