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

  1. Tell Kadir. He can fix it in Verbatim.
  2. Once it's fixed, push to production. This will pick up the
     new strings.

* If Ricky or Will or someone with commit access to svn is around:

  1. Tell that person. She/he can fix it in svn.
  2. Once it's fixed, push to production. This will pick up the
     new strings.
  3. Tell Kadir or Milos so they can fix Verbatim.
