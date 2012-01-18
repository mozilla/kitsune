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
* We can fine-tune the algorithm ourselves.


.. Note::

   Right now we're rewriting our search system to use Elastic and
   switching between Sphinx and Elastic.  At some point, the results
   we're getting with our Elastic-based code will be good enough to
   switch over.  At that point, we'll remove the Sphinx-based search
   code.

   Until then, we have instructions for installing both Sphinx Search
   and Elastic Search.

   **To switch between Sphinx Search and Elastic Search**, there's a
   waffle flag.  In the admin, go to waffle, then turn on and off the
   ``elasticsearch`` waffle flag.  If it's on, then Elastic is used.
   If it's off, then Sphinx is used.


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


Installing Elastic Search
=========================

There's an installation guide on the Elastic Search site.

http://www.elasticsearch.org/guide/reference/setup/installation.html

The directory you install Elastic in will hereafter be referred to as
``ELASTICDIR``.

You can configure Elastic Search with the configuration file at
``ELASTICDIR/config/elasticsearch.yml``.

Elastic Search uses two settings in ``settings.py`` that you can
override in ``settings_local.py``::

    # Connection information for Elastic
    ES_HOSTS = ['127.0.0.1:9200']
    ES_INDEXES = {'default': 'sumo'}


.. Warning::

   The host setting must match the host and port in
   ``ELASTICDIR/config/elasticsearch.yml``.  So if you change it in
   one place, you must also change it in the other.

There are a few other settings you can set in your ``settings_local.py``
file that override Elastic Utils defaults.  See `the Elastic Utils
docs <http://elasticutils.readthedocs.org/en/latest/installation.html#configure>`_
for details.

Other things you can change:

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

    Defaults to 20.

    This affects all index-related operations including creating
    indexes, deleting indexes, creating mappings, indexing documents
    and calling flush_bulk.

    If you're having problems with indexing operations timing out,
    raising this number can sometimes help.


.. Note::

   Don't have a lot of memory? Having problems with indexing running
   for 20 minutes and then dying in an overly dramatic firesplosion?

   Try setting::

      ES_INDEXING_TIMEOUT = 60
      ES_FLUSH_BULK_EVERY = 10


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

This will delete the existing indexes, create new ones, and reindex
everything in your database.  On my machine it takes about an hour.

If you need to get stuff done and don't want to wait for a full indexing,
you can index a percentage of things.

For example, this indexes 10% of your data ordered by id::

    $ ./manage.py esreindex --percent 10

This indexes 50% of your data ordered by id::

    $ ./manage.py esreindex --percent 50

I use this when I'm fiddling with mappings and the indexing code.

Also, you can index specific doctypes. Doctypes are named are the
``_meta.db_table`` of the model they map to. At the time of this writing,
there are three doctypes:

* questions_question
* wiki_document
* forums_thread

You can index specific doctypes by specifying the doctypes on the command
line. This reindexes just questions::

    $ ./manage.py esreindex questions_question


.. Note::

   Once you've indexed everything, you won't have to do it again unless
   indexing code changes.  The models have ``post_save`` and ``pre_delete``
   hooks that will update the index as the data changes.


Health/statistics
-----------------

You can see Elastic Search statistics/health with::

    $ ./manage.py eswhazzup

The last few lines tell you how many documents are in the index by doctype.
I use this to make sure I've got stuff in my index.
