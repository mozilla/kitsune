.. _osumo-chapter:

============
Offline SUMO
============


Overview
========

Offline SUMO is an app developed for Firefox OS (and other platforms if so
desired) that serves SUMO contents offline. This document is written for
developers who wish to hack on the app. As of right now, the offline SUMO's
code lives under https://github.com/mozilla/osumo.

Offline SUMO is to be ran entirely offline. The primary target is a low powered
device such as a Firefox OS phone. This requirement subject the app to some
constraints:

- App needs to be developed to run offline entirely, with the exception of the
  initial installation.
- App needs to run reasonably fast on a low powered device such as a Firefox OS
  phone.
- App needs to be mobile friendly.

The following choices are made to accomodate these constraints:

- App is written as a single page application with Angular.JS. Data is to
  be downloaded from SUMO's offline API and stored into IndexedDB. This
  resolves most of the needs for a reasonably fast, offline only app. The
  caching of HTML, CSS, and JavaScript files are done via appcache.
- The app is to mirror the current mobile design. However as of this point the
  app only has an experimental Foundation based theme.
- Most of the heavy lifting of the database generation is done on the server.
  The data returned from the server is to be directly stored into IndexedDB
  with no further modifications.

App Structure
=============

The client side has a small server that serves HTML for essentially all urls.
The same HTML will be served and Angular.JS will take care of rendering the UI.
The server also serves all the static files and builds the JavaScript and other
files that needs to be generated.

Most of the interesting code lives under static/js/develop/ and static/partials/.

Database Structure
==================

All data is stored in IndexedDB. The different databases and object stores that
are used are listed here:

Databases
---------

:Name:
    osumo-settings
:Purpose:
    To store metadata, settings data, and locales
:Stores:
    meta, locales
:Notes:
    This database will always have a version of 1 for now. Changing this should
    be okay but let's try to avoid doing that.

------------------

:Name:
    osumo
:Purpose:
    The main database (storing documents, everything necessary to display).
:Stores:
    locales, docs, topics, indexes, images
:Notes:
    All data that actually matters lives in this database.

Object Stores
-------------

**Meta store under osumo-settings**

:Name:
    meta
:Parent:
    osumo-settings
:Purpose:
    To store some metadata about the app.
:Key path:
    version (int)
:Schema:

    ::

      {
        version: the version of the app (int),
        locale: the locale code that's the default display locale (str)
      }

**Locales store under osumo-settings**

:Name:
    locales
:Parent:
    osumo-settings
:Purpose:
    To store translations for i18n.
:Key path:
    locale (str)
:Schema:

    ::

      {
        locale: locale code (str),
        name: locale's display name (str),
        data: {
          english str: translated str (str)
        }
      }
:Notes:
    This might go away as the i18n component is still pretty unstable.

----------------------------

**Locales store under osumo**

:Name:
    locales
:Parent:
    osumo
:Purpose:
    To store the locales downloaded and the topics/products they have.
:Key path:
    key (str)
:Schema:

    ::

      {
        key: locale code (str),
        name: The display name (str),
        products: [
          {
            slug: product slug (str),
            name: product display name (str)
          }
        ],
        children: [
          topic slug (str)
        ]
      }

**Topics store under osumo**

:Name:
    topics
:Parent:
    osumo
:Purpose:
    To store the list of topics and the associated articles for that topic.
:Key path:
    key (str)
:Schema:

    ::

      {
        key: locale + "~" + product slug + "~" + topic slug (str),
        name: topic display name (str),
        product: product slug (str),
        children: [
          subtopic slug (str)
        ],
        slug: topic slug
      }
:Index:
    ``product`` is indexed by the field ``by_product``

**Docs store under osumo**

:Name:
    docs
:Parent:
    osumo
:Purpose:
    To store the documents.
:Key path:
    key (str)
:Schema:

    ::

      {
        key: locale + "~" + doc slug (str),
        id: unique unique id from db (int),
        html: the html content (str),
        slug: document slug (str),
        title: document title (str),
        updated: the last time the document has been updated as seconds since UNIX epoch (int)
      }
:Index:
    ``id`` is indexed by the field ``by_id``

**Indexes store under osumo**

:Name:
    indexes
:Parent:
    osumo
:Purpose:
    To store the index for offline search.
:Key path:
    key (str)
:Schema:

    ::

      {
        key: locale + "~" + product slug (str),
        index: {
          word: [
            [doc id (int), score (float)]
          ]
        }
      }
:Notes:
    More on how this works in the `Offline Search`_ section.

Offline Search
==============

Searching is a feature that we need offline as it is an important way to find
articles. Before designing the search engine, several key constraints are
considered:

- Search needs to run entirely offline.
- Search needs to be *reasonably good* and it should be able to handle
  multi-word queries. This means ranking will be somewhat important.
- Search needs to be *reasonably fast* on a low powered device such as a
  Firefox OS phone.
- Index data must be stored offline (if any) and it must be stored into
  indexeddb as it is the only viable option.

To address these issues, the following approach is taken:

- The indexing operation is done entirely server side. The client side only
  needs to perform the minimum amount of computation.
- The index chosen is a reverse hashtable and the corpus is just the titles and
  summaries of articles. They usually have a fairly good description of what
  the article is about. A reverse hashtable is also easily serialized into JSON
  and stored into IndexedDB.

We do not provide (yet!):

- Stemming: it is difficult to provide stemming to many languages uniformly.
- Aliasing characters such as e to é: This may be added in soon.

Index Structure
---------------

The index chosen is a reverse hashtable. That is, every word is mapped to a
list of documents that it occurs in. In addition, there is a score that each
word has for each document that it appears in. The higher the score, the more
important that word is.

The score is computed based on an algorithm called
`TF-IDF <http://en.wikipedia.org/wiki/Tf%E2%80%93idf>`_. TFIDF is an algorithm
that scores the importance of each word in an article given a corpus of many
articles. It effectively extracts the most important words in any article. For
us, we multiply the scores for the terms of the title by 1.2, effectively
weighting it more than the summary.

For each search term, we go through the index and finds the list of document
and scores the term is associated with. We add up the score for each article
and sorts them. The document with the highest score will be displayed at the
top and the document with the lowest score will be displayed at the bottom.

As an example, if we have the following index:

    ::

      {
        "bookmarks": [1029, 2.3, 1000, 1.5],
        "firefox": [1000, 0.9, 1010, 0.7, 1111: 0.8]
      }

and if we searched for the term "firefox bookmarks", the following is computed:

    ::

      [
        [1000, 2.4], // 1.5 + 0.9 from bookmarks and firefox
        [1029, 2.3],
        [1111, 0.8],
        [1010, 0.7]
      ]

These documents will be displayed with that order.

Component on Kitsune
====================

The offline sumo app requires a component on Kitsune as we need to be able to
get the data from the production wiki. Currently, one route is provided:
/offline/get-bundles. This url will return a bundle that is to be directly
stored into client sides' IndexedDB. The details of this structure is detailed
in `Database Structure`_.
