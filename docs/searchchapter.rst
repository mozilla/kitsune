.. _search-chapter:

======
Search
======

Kitsune is in the process of switching from `Sphinx Search
<http://www.sphinxsearch.com>`_ to `Elastic Search
<http://www.elasticsearch.org/>`_ to power its on-site search
facility.

Both of these give us a number of advantages over MySQL's full-text
search or Google's site search.

* Much faster than MySQL.

  * And reduces load on MySQL.

* We have total control over what results look like.
* We can adjust searches with non-visible content.
* We don't rely on Google reindexing the site.
* We can fine-tune the algorithm and scoring.


.. Note::

   We've deprecated the Sphinx search code as replaced by our Elastic
   Search code.

   To run the unit tests, you still need both installed. (Note: That
   should get fixed.)

   To test search locally, you should test with Elastic Search.

   At some point in the near future we will remove Sphinx search from
   the system altogether.

   **To switch between Sphinx Search and Elastic Search**, there's a
   waffle flag.  In the admin, go to waffle, then turn on and off the
   ``elasticsearch`` waffle flag.  If it's on, then Elastic is used.
   If it's off, then Sphinx is used.


Installing Elastic Search
=========================

There's an installation guide on the Elastic Search site.

http://www.elasticsearch.org/guide/reference/setup/installation.html

We're currently using 0.17.something in production.

The directory you install Elastic in will hereafter be referred to as
``ELASTICDIR``.

You can configure Elastic Search with the configuration file at
``ELASTICDIR/config/elasticsearch.yml``.

Elastic Search uses several settings in ``settings.py`` that you
should override in ``settings_local.py``::

    # Connection information for Elastic
    ES_HOSTS = ['127.0.0.1:9200']
    ES_INDEXES = {'default': 'sumo'}
    ES_WRITE_INDEXES = ES_INDEXES


``ES_HOSTS``

    No default.

    Points to the ip address and port for your Elastic Search
    instance.

    .. Warning::

       The host setting must match the host and port in
       ``ELASTICDIR/config/elasticsearch.yml``. So if you change it
       in one place, you must also change it in the other.


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


There are a few other settings you can set in your ``settings_local.py``
file that override Elastic Utils defaults.  See `the Elastic Utils
docs <http://elasticutils.readthedocs.org/en/latest/installation.html#configure>`_
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
    ``settings_local.py`` file. This affects whether Kitsune does
    Elastic indexing when data changes in the ``post_save`` and
    ``pre_delete`` hooks.

    For tests, ``ES_LIVE_INDEXING`` is set to ``False`` except for
    Elastic specific tests so we're not spending a ton of time
    indexing things we're not using.

``ES_FLUSH_BULK_EVERY``

    Defaults to 100.

    We do bulk indexing meaning we queue up a bunch and then push them
    through all at the same time. This requires memory to queue them,
    so if you've got low memory, dropping this value to something
    lower (but still greater than 1) could help.

``ES_TIMEOUT``

    Defaults to 5.

    This affects timeouts for search-related requests.

    If you're having problems with ES being slow, raising this number
    can be helpful.

``ES_INDEXING_TIMEOUT``

    Defaults to 30.

    This affects all index-related operations including creating
    indexes, deleting indexes, creating mappings, indexing documents
    and calling flush_bulk.

    If you're having problems with indexing operations timing out,
    raising this number can sometimes help. Try 60.

``ES_DUMP_CURL``

    This defaults to None.

    This is super handy for debugging our Elastic Search code and
    otherwise not useful for anything else. See the `elasticutils
    documentation
    <http://elasticutils.readthedocs.org/en/latest/debugging.html#es-dump-curl>`_.



Using Elastic Search
====================

Running
-------

Start Elastic Search by::

    $ ELASTICDIR/bin/elasticsearch

That launches Elastic Search in the background.


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


Health/statistics
-----------------

You can see Elastic Search index status with::

    $ ./manage.py esstatus

This lists the indexes, tells you which ones are set to read and
write, and tells you how many documents are in the indexes by mapping
type.


Deleting indexes
----------------

You can use the search admin to delete the index.

On the command line, you can do::

    $ ./manage.py esdelete <index-name>



Tools
-----

One tool that's helpful for Elastic Search work is `elasticsearch-head
<https://github.com/mobz/elasticsearch-head>`_. It's like the
phpmyadmin for Elastic Search.


Implementation details
----------------------

Kitsune uses `elasticutils
<https://github.com/davedash/elasticutils>`_ and `pyes
<https://github.com/aparo/pyes>`_.

Most of our code is in the ``search`` app in ``apps/search/``.

Models in Kitsune that are indexable use ``SearchMixin`` defined in
``models.py``.

Utility functions are implemented in ``es_utils.py``.

Sub commands for ``manage.py`` are implemented in
``management/commands/``.


Search Scoring
==============

These are the defaults that apply to all searches:

kb:

    query fields: title, content, summary, keywords

questions:

    query fields: title, question_content, answer_content

forums:

    query fields: title, content


.. Note::

   We can do boosts/weights, but currently there is no
   boosting/weighting done.


Elastic Search is built on top of Lucene so the `Lucene documentation
on scoring <http://lucene.apache.org/java/3_5_0/scoring.html>`_ covers
how a document is scored in regards to the search query and its
contents. The weights modify that---they're query-level boosts.

Additionally we use a series of filters on tags, q_tags, and other
properties of the documents like has_helpful, is_locked, is_archived,
etc, In Elastic Search, filters remove items from the result set, but
don't otherwise affect the scoring.


Front page search
-----------------

A front page search is what happens when you start on the front page,
enter in a search query in the search box, and click on the green
arrow.

Front page search does the following:

1. searches only kb and questions
2. (filter) kb articles are tagged with the product (e.g. "desktop")
3. (filter) kb articles must not be archived
4. (filter) kb articles must be in Troubleshooting (10) and
   How-to (20) categories
5. (filter) questions are tagged with the product (e.g. "desktop")
6. (filter) questions must have an answer marked as helpful


It scores as specified above.


Advanced search
---------------

The advanced search form lines up with the filters applied.

For example, if you search for knowledge base articles in the
Troubleshooting category, then we add a filter where the result has to
be in the Troubleshooting category.


Link to the Elastic Search code
-------------------------------

Here's a link to the search view in the master branch. This is what's
on dev:

https://github.com/mozilla/kitsune/blob/master/apps/search/views.py


Here's a link to the search view in the next branch. This is what's
on staging:

https://github.com/mozilla/kitsune/blob/next/apps/search/views.py


Installing Sphinx Search
========================

We currently require **Sphinx 0.9.9**. You may be able to install this from a
package manager like yum, aptitude, or brew.

If not, you can easily `download <http://sphinxsearch.com/downloads/>`_ the
source and compile it. Generally all you'll need to do is::

    $ cd sphinx-0.9.9
    $ ./configure --enable-id64  # Important! We need 64-bit document IDs.
    $ make
    $ sudo make install

This should install Sphinx in ``/usr/local/bin``. (You can change this by
setting the ``--prefix`` argument to ``configure``.)

To test that everything works, make sure that the ``SPHINX_INDEXER`` and
``SPHINX_SEARCHD`` settings point to the ``indexer`` and ``searchd`` binaries,
respectively. (Probably ``/usr/local/bin/indexer`` and
``/usr/local/bin/searchd``, unless you changed the prefix.) Then run the
Kitsune search tests::

    $ ./manage.py test -s --no-input --logging-clear-handlers search

If the tests pass, everything is set up correctly!


Using Sphinx Search
===================

Having Sphinx installed will allow the search tests to run, which may be
enough. But you want to work on or test the search app, you will probably need
to actually see search results!


The Easy, Sort of Wrong Way
---------------------------

The easiest way to start Sphinx for testing is to use some helpful management
commands for developers::

    $ ./manage.py reindex
    $ ./manage.py start_sphinx

You can also stop Sphinx::

    $ ./manage.py stop_sphinx

If you need to update the search indexes, you can pass the ``--rotate`` flag to
``reindex`` to update them in-place::

    $ ./manage.py reindex --rotate

While this method is very easy, you will need to reindex after any time you run
the search tests, as they will overwrite the data files Sphinx uses.


The Complicated but Safe Way
----------------------------

You can safely run multiple instances of ``searchd`` as long as they listen on
different ports, and store their data files in different locations.

The advantage of this method is that you won't need to reindex every time you
run the search tests. Otherwise, this should be identical to the easy method
above.

Start by copying ``configs/sphinx`` to a new directory, for example::

    $ cp -r configs/sphinx ../
    $ cd ../sphinx

Then create your own ``localsettings.py`` file::

    $ cp localsettings.py-dist localsettings.py
    $ vim localsettings.py

Fill in the settings so they match the values in ``settings_local.py``. Pick a
place on the file system for ``ROOT_PATH``.

Once you have tweaked all the settings so Sphinx will be able to talk to your
database and write to the directories, you can run the Sphinx binaries
directly (as long as they are on your ``$PATH``)::

    $ indexer --all -c sphinx.conf
    $ searchd -c sphinx.conf

You can reindex without restarting ``searchd`` by using the ``--rotate`` flag
for ``indexer``::

    $ indexer --all --rotate -c sphinx.conf

You can also stop ``searchd``::

    $ searchd --stop -c sphinx.conf

This method not only lets you maintain a running Sphinx instance that doesn't
get wiped out by the tests, but also lets you see some very interesting output
from Sphinx about indexing rate and statistics.
