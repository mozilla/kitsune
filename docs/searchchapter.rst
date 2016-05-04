.. _search-chapter:

======
Search
======

Kitsune uses `Elasticsearch <https://www.elastic.co/>`_ to
power its on-site search facility.

It gives us a number of advantages over MySQL's full-text search or
Google's site search.

* Much faster than MySQL.

  * And reduces load on MySQL.

* We have total control over what results look like.
* We can adjust searches with non-visible content.
* We don't rely on Google reindexing the site.
* We can fine-tune the algorithm and scoring.


Installing Elasticsearch
========================

There's an installation guide on the Elasticsearch site:

https://www.elastic.co/guide/en/elasticsearch/reference/1.3/setup-service.html

We're currently using `1.2.4 <https://www.elastic.co/downloads/past-releases/elasticsearch-1-2-4>`_
in production.

The directory you install Elasticsearch in will hereafter be referred
to as ``ELASTICDIR``.

You can configure Elasticsearch with the configuration file at
``ELASTICDIR/config/elasticsearch.yml``.

Elasticsearch uses several settings in ``kitsune/settings.py`` that you
need to override in ``kitsune/settings_local.py``. Here's an example::

    # Connection information for Elastic
    ES_URLS = ['http://127.0.0.1:9200']
    ES_INDEXES = {'default': 'sumo_dev'}
    ES_WRITE_INDEXES = ES_INDEXES


These settings explained:

``ES_URLS``

    Defaults to ``['http://127.0.0.1:9200']``.

    Points to the url for your Elasticsearch instance.

    .. Warning::

       The url must match the host and port in
       ``ELASTICDIR/config/elasticsearch.yml``. So if you change it in
       one place, you must also change it in the other.


``ES_INDEXES``

    Mapping of ``'default'`` to the name of the index used for
    searching.

    The index name must be prefixed with the value of
    ``ES_INDEX_PREFIX``.

    Examples if ``ES_INDEX_PREFIX`` is set to ``'sumo'``::

        ES_INDEXES = {'default': 'sumo'}
        ES_INDEXES = {'default': 'sumo_20120213'}

        ES_INDEXES = {'default': 'tofurkey'}  # WRONG!


``ES_WRITE_INDEXES``

    Mapping of ``'default'`` to the name of the index used for
    indexing.

    The index name must be prefixed with the value of
    ``ES_INDEX_PREFIX``.

    Examples if ``ES_INDEX_PREFIX`` is set to ``'sumo'``::

        ES_WRITE_INDEXES = ES_INDEXES
        ES_WRITE_INDEXES = {'default': 'sumo'}
        ES_WRITE_INDEXES = {'default': 'sumo_20120213'}

        ES_WRITE_INDEXES = {'default': 'tofurkey'}  # WRONG!

    .. Note::

       The separate roles for indexes allows us to push mapping
       changes to production. In the first push, we'll push the
       mapping change and give ``ES_WRITE_INDEXES`` a different
       value. Then we reindex into the new index. Then we push a
       change updating ``ES_INDEXES`` to equal ``ES_WRITE_INDEXES``
       allowing the search code to use the new index.

       If you're a developer, the best thing to do is have your
       ``ES_WRITE_INDEXES`` be the same as ``ES_INDEXES``. That way
       you can reindex and search and you don't have to fiddle with
       settings in between.


There are a few other settings you can set in your
``kitsune/settings_local.py`` file that override ElasticUtils defaults.  See
`the ElasticUtils docs
<https://elasticutils.readthedocs.io/en/latest/django.html#configuration>`_
for details.

Other things you can change:

``ES_INDEX_PREFIX``

    Defaults to ``'sumo'``.

    All indexes for this application must start with the index
    prefix. Indexes that don't start with the index prefix won't show
    up in index listings and cannot be deleted through the esdelete
    subcommand and the search admin.

    .. Note::

       The index names in both ``ES_INDEXES`` and ``ES_WRITE_INDEXES``
       **must** start with this prefix.

``ES_LIVE_INDEXING``

    Defaults to False.

    You can also set ``ES_LIVE_INDEXING`` in your
    ``kitsune/settings_local.py`` file. This affects whether Kitsune does
    Elasticsearch indexing when data changes in the ``post_save`` and
    ``pre_delete`` hooks.

    For tests, ``ES_LIVE_INDEXING`` is set to ``False`` except for
    Elasticsearch specific tests so we're not spending a ton of time
    indexing things we're not using.

``ES_TIMEOUT``

    Defaults to 5.

    This affects timeouts for search-related requests.

    If you're having problems with ES being slow, raising this number
    might be helpful.


Using Elasticsearch
===================

Running
-------

Start Elasticsearch by::

    $ ELASTICDIR/bin/elasticsearch

That launches Elasticsearch in the background.


Indexing
--------

Do a complete reindexing of everything by::

    $ ./manage.py esreindex

This will delete the existing index specified by ``ES_WRITE_INDEXES``,
create a new one, and reindex everything in your database. On my
machine it takes under an hour.

If you need to get stuff done and don't want to wait for a full
indexing, you can index a percentage of things.

For example, this indexes 10% of your data ordered by id::

    $ ./manage.py esreindex --percent 10

This indexes 50% of your data ordered by id::

    $ ./manage.py esreindex --percent 50

I use this when I'm fiddling with mappings and the indexing code.

You can also specify which models to index::

    $ ./manage.py esreindex --models questions_question,wiki_document

See ``--help`` for more details::

    $ ./manage.py esreindex --help


.. Note::

   Once you've indexed everything, if you have ``ES_LIVE_INDEXING``
   set to ``True``, you won't have to do it again unless indexing code
   changes. The models have ``post_save`` and ``pre_delete`` hooks
   that will update the index as the data changes.


.. Note::

   If you kick off indexing with the admin, then indexing gets done in
   chunks by celery tasks. If you need to halt indexing, you can purge
   the tasks with::

       $ ./manage.py celeryctl purge

   If you do this often, it helps to write a shell script for it.


Health/statistics
-----------------

You can see Elasticsearch index status with::

    $ ./manage.py esstatus

This lists the indexes, tells you which ones are set to read and
write, and tells you how many documents are in the indexes by mapping
type.


Deleting indexes
----------------

You can use the search admin to delete the index.

On the command line, you can do::

    $ ./manage.py esdelete <index-name>


Implementation details
----------------------

Kitsune uses `elasticutils <https://github.com/mozilla/elasticutils>`_
and `pyelasticsearch
<https://pyelasticsearch.readthedocs.io/en/latest/>`_.

Most of our code is in the ``search`` app in ``kitsune/search/``.

Models in Kitsune that are indexable use ``SearchMixin`` defined in
``models.py``.

Utility functions are implemented in ``es_utils.py``.

Sub commands for ``manage.py`` are implemented in
``management/commands/``.


Searching on the site
=====================

Scoring
-------

These are the default weights that apply to all searches:

wiki (aka kb)::

    document_title__match           6
    document_content__match         1
    document_keywords__match        8
    document_summary__match         2

questions (aka support forums)::

    question_title__match           4
    question_content__match         3
    question_answer_content__match  3

forums (aka contributor forums)::

    post_title__match               2
    post_content__match             1


Elasticsearch is built on top of Lucene so the `Lucene documentation
on scoring
<http://lucene.apache.org/core/old_versioned_docs/versions/3_5_0/scoring.html>`_
covers how a document is scored in regards to the search query and its
contents. The weights modify that---they're query-level boosts.

Additionally, `this blog post from 2006 <http://www.supermind.org/blog/378>`_
is really helpful in terms of providing insight on the implications of
the way things are scored.


Filters
-------

We use a series of filters on document_tag, question_tag, and other
properties of documents like `has_helpful`, `is_locked`, `is_archived`,
etc.

In ElasticSearch, filters remove items from the result set, but don't
affect the scoring.

We cannot apply weights to filtered fields.


Regular search
--------------

A `regular` search is any search that doesn't start from the `Advanced
Search` form.

You could start a `regular` search from the front page or from the
search form on any article page.

Regular search does the following:

1. searches only kb and support forums
2. (filter) kb articles are tagged with the product (e.g. "desktop")
3. (filter) kb articles must not be archived
4. (filter) kb articles must be in Troubleshooting (10) and
   How-to (20) categories
5. (filter) support forum posts tagged with the product
   (e.g. "desktop")
6. (filter) support forum posts must have an answer marked as helpful
7. (filter) support forum posts must not be archived

It scores as specified above.


Ask A Question search
---------------------

An `Ask a question` or `AAQ` search is any search that is performed within
the AAQ workflow. The only difference to `regular` search is that `AAQ`
search shows forum posts that have no answer marked as helpful.


Advanced search
---------------

The `advanced` search is any search that starts from the `Advanced
Search` form.

The advanced search is defined by whatever you specify in the
`Advanced Search` form.

For example, if you search for knowledge base articles in the
Troubleshooting category, then we add a filter where the result has to
be in the Troubleshooting category.


Link to the Elasticsearch code
------------------------------

Here's a link to the search view in the master branch:

https://github.com/mozilla/kitsune/blob/master/kitsune/search/views.py
