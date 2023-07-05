===
SEO
===

This document covers notes and policies related to SEO.

Prefer ``meta`` tag if possible
===============================

If an entire page should not be indexed, and/or none of its links
followed, prefer to use the ``<meta name="robots" ...>`` tag by specifying
something like::

    {% set meta = (('robots', 'noindex'),) %}

or::

    {% set meta = (('robots', 'noindex, nofollow'),) %}


within the lowest-level Jinja2 templates of the inheritance chain that
apply to only the desired pages.

However, if you only want to discourage the crawling of specific links within
a page, you'll have to add ``rel="nofollow"`` to each of those links within its
template. For example::

    <a rel="nofollow" href="...">...</a>


Breadcrumbs
===========

If one or more of the breadcrumb links for a page should not be crawled, you
can add an extra string to those breadcrumb tuples to specify the proper
attribute to use, for example::

    {% set crumbs = [((profile_url(user), 'rel="nofollow"'), user.username), (None, title)] %}

or::

    {% set crumbs = [(document.get_absolute_url(), document.title), ((url('wiki.discuss.threads', document.slug), 'rel="ugc nofollow"'), _('Discuss'))] %}

KB Forums
=========

KB forums are user-generated content about KB articles. They are not
official content, and therefore not meant to be searchable. All links to
KB forums should be marked with ``rel="ugc nofollow"``.

User Links
==========

User-related pages are also not meant to be indexed (searchable), and links
to them should not be crawled, so the base user template
(``kitsune/users/jinja2/users/base.html``) contains::

    {% set meta = (('robots', 'noindex'),) %}

and all user links on all pages should be marked with ``rel="nofollow"``.
