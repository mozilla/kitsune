.. _wiki-chapter:

========================
Important Wiki Documents
========================

There are a number of "important" wiki documents, i.e. documents with
well-known names that are used in parts of the interface besides the normal
knowledge base.

These documents make it possible to update content on, for example, the home
pages without requiring code changes.

In all cases, the title of the English document matters, but the slug, or title
of the localized versions, does not.


Home page - Quick
=================

Content for the left, narrow column of the home page (``/home``). Use
``<section>`` tags to break up sections and ``= h1 =`` wiki markup within the
sections for headings.


Home page - Explore
===================

Content for the right, wide column of the home page (``/home``). Use
``<section>`` tags to break up sections that can wrap and ``== h2 ==`` wiki
markup within the sections for headings.


Mobile home - Quick
===================

Identical to **Home page - Quick** except used on the mobile home page
(``/mobile``).


Mobile home - Explore
=====================

Identical to **Home page - Explore** except used on the mobile home page
(``/mobile``).


Desktop home for mobile - Common Questions
==========================================

A long name for a short document: this provides content for the "Common
Questions" section of the desktop home page (``/home``) while on a mobile
device. It should be an unordered list (i.e. ``<ul>`` or ``* item``) with
nothing else. The list items are usually links to other KB documents.


Mobile home for mobile - Common Questions
=========================================

Exactly like **Desktop home for mobile - Common Questions** except it provides
content for the "Common Questions" section of the mobile home page
(``/mobile``) while on a mobile device.
