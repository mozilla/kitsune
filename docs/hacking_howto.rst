.. _hacking-howto-chapter:

==============================
Hacking HOWTO for Contributors
==============================

.. contents::
   :local:


Summary
=======

This chapter helps you get a minimal installation of Kitsune up and
running to make it easier to contribute.

If you're setting Kitsune up for deployment, instead of development, make
sure you read all the way to the end and then read the additional sections.

If you have any problems getting Kitsune running, let us know. See the
:ref:`contact-us-chapter`.


Operating systems
=================

Windows
-------

If you're using Windows as your operating system, you'll need to set
up a virtual machine and run Kitsune in that. Kitsune won't run in
Windows.

If you've never set up a virtual machine before, let us know and we
can walk you through it. Having said that, it's not easy to do for
people who haven't done it before.


Mac OSX
-------

Just follow along with the instructions below. Several of us use OSX,
so if you run into problems, let us know.


Linux
-----

We know these work in Debian, Ubuntu, Arch, and will probably work in other
distributions. It's likely that you'll encounter some steps that are
slightly different. If you run into problems, let us know.


Requirements
============

These are required for the minimum installation:

* git
* Python 2.6 or 2.7
* pip: `<http://www.pip-installer.org/en/latest/>`_
* virtualenv
* MariaDB 5.5 server and client headers
* Memcached Server
* libxml and headers
* libxslt and headers
* libjpeg and headers
* zlib and headers

These are optional:

* Redis
* ElasticSearch: :ref:`search-chapter`

Installation for these is very system dependent. Using a package
manager, like yum, aptitude, or brew, is encouraged.

.. _hacking-howto-memcached:

memcached
---------

You need to have memcached running. Otherwise CSRF stuff won't work.

If you are running OSX and using homebrew, you can do something like::

    $ brew install memcached


and launch it::

    $ memcached


If you are running RedHat/CentOS/Fedora, once you have installed
memcached you can start it and configure it to run on startup using::

    $ chkconfig memcached on
    $ /etc/init.d/memcached start
    $ service memcached start


.. Note::

   This should probably be somewhere else, but the easy way to flush
   your cache is something like this::

       echo "flush_all" | nc localhost 11211


   Assuming you have memcache configured to listen to 11211.


Getting the Source
==================

Grab the source from Github using::

    $ git clone --recursive https://github.com/mozilla/kitsune.git
    $ cd kitsune


.. Note::

   If you forgot to add ``--recursive``, you can still get all the
   submodules with::

       $ git submodule update --init --recursive


Setting up an Environment
=========================

It is strongly recommended to run Kitsune in a virtual environment, which is a
tool to isolate Python environments from eachother and the system. It makes
local development much easier, especially when working on multiple projects.

To create a virtual environment::

    $ virtualenv venv

which creates a virtualenv named "venv" in your current directory (which should
be the root of the git repo. Now activate the virtualenv::

    $ source venv/bin/activate

You'll need to run this command every time you work on Kitsune, in every
terminal window you use.


Installing dependencies
=======================

Compiled Packages
-----------------

There are a small number of compiled packages, including the MySQL
Python client.

For development, you should install these with ``pip``, but for
other situations you may want to use your system package manager.

::
    $ pip install -r requirements/compiled.txt

If you want to use your system's package manager, you'll need to go
through ``requirements/compiled.txt`` and install the dependencies by
hand.


Python Packages
---------------

All the pure-Python requirements are provided in the ``vendor``
directory, also known as the "vendor library". This makes the packages
available to Python without installing them globally and keeps them
pinned to known-compatible versions.

If you do not have a vendor library, see the section about getting the source
above.

See the :ref:`vendor library <vendor-chapter>` documentation for more
information on getting the vendor lib and keeping it up to date.

Javascript Packages
-------------------

Kitsune relies on a small number of Javascript packages. To get those, you will
need to `install Node.JS and NPM
<https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager>`_.

Now install the javascript dependencies with::

    $ npm install

This should create a directory named ``node_modules`` in your git repo.


Configuration and Setup
=======================

settings_local.py
-----------------

Create a file named ``settings_local.py`` in the ``kitsune/`` directory.
Start with this::

    from kitsune.settings import *

    DEBUG = True
    TEMPLATE_DEBUG = DEBUG
    SESSION_COOKIE_SECURE = False

    # Allows you to run Kitsune without running Celery---all tasks
    # will be done synchronously.
    CELERY_ALWAYS_EAGER = True

    # Allows you to specify waffle settings in the querystring.
    WAFFLE_OVERRIDE = True

    # Change this to True if you're going to be doing search-related
    # work.
    ES_LIVE_INDEXING = False

    # Basic cache configuration for development.
    CACHES = {
        'default': {
            'BACKEND': 'caching.backends.memcached.CacheClass',
            'LOCATION': 'localhost:11211',
            'PREFIX': 'sumo:',
            }
        }

    # Basic database configuration for development.
    DATABASES = {
        'default': {
            'NAME': 'kitsune',
            'ENGINE': 'django.db.backends.mysql',
            'HOST': 'localhost',
            'USER': 'kitsune',
            'PASSWORD': '<YOUR_PASSWORD>',
            'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
            'TEST_CHARSET': 'utf8',
            'TEST_COLLATION': 'utf8_unicode_ci',
            },
        }

    LESS_PREPROCESS = True
    LESS_BIN = '/path/to/kitsune/node_modules/less/bin/lessc'

    # Tells django-axes we aren't behind a reverse proxy.
    AXES_BEHIND_REVERSE_PROXY = False


Don't forget to change ``<YOUR_PASSWORD>`` and update ``LESS_BIN``
based on your setup.

Note the two settings ``TEST_CHARSET`` and ``TEST_COLLATION``. Without
these, the test suite will use MySQL's (moronic) defaults when
creating the test database (see below) and lots of tests will
fail. Hundreds.

Now you can copy and modify any settings from ``kitsune/settings.py`` into
``kitsune/settings_local.py`` and the value will override the default.


Database
--------

You defined a database connection in ``kitsune/settings_local.py``.

Now create the database and grant permissions to the user, based on your
database settings. For example, using the settings above::

    $ mysql -u root -p
    mysql> CREATE DATABASE kitsune CHARACTER SET utf8 COLLATE utf8_unicode_ci;
    mysql> GRANT ALL ON kitsune.* TO kitsune@localhost IDENTIFIED BY '<YOUR_PASSWORD>';


To initialize the database, do::

    $ ./manage.py syncdb --migrate


This will ask you to create a superuser account. Just follow the prompts.

You'll now have an empty but up-to-date database!

After logging in, you can create a profile for the user by going to
``/users/edit`` in your browser.

See also the :ref:`important wiki documents <wiki-chapter>`
documentation.


Install Sample Data
-------------------

We include some sample data to get you started. You can install it by
running this command::

    $ ./manage.py generatedata


Product Details Initialization
------------------------------

One of the packages Kitsune uses, ``product_details``, needs to fetch
JSON files containing historical Firefox version data and write them
within its package directory. To set this up, run this command to do
the initial fetch::

    $ ./manage.py update_product_details


Testing it out
==============

To start the dev server, run ``./manage.py runserver``, then open up
``http://localhost:8000``.

If everything's working, you should see a somewhat empty version of
the SUMO home page!

.. Note::

   If you see an unstyled site and empty CSS files, you have to remove
   all empty files having a ``.less.css`` since they are empty and
   should be regenerated.

   To do this, run the following command on the top directory
   of your Kitsune clone::

       $ find . -name "*.less.css" -delete


  Verify the ``LESS_BIN`` setting in settings_local.py.
  Then *hard-refresh* your pages on the browser via *Ctrl + Shift + R*.


Setting it up
-------------

A great way to check that everything really is working is to run the
test suite. You'll need to add an extra grant in MySQL for your
database user::

    $ mysql -u root -p
    mysql> GRANT ALL ON test_kitsune.* TO kitsune@localhost IDENTIFIED BY '<YOUR_PASSWORD>';


The test suite will create and use this database, to keep any data in
your development database safe from tests.


Running the tests
-----------------

Running the test suite is easy::

    $ ./manage.py test -s --noinput --logging-clear-handlers

This may open a Firefox window, which will close automatically.

For more information, see the :ref:`test documentation
<tests-chapter>`.


Trouble-shooting
================

Error: A csrf_token was used in a template, but the context did not provide the value
-------------------------------------------------------------------------------------

If you see this, you likely have CACHES specifying to use memcached in your
``kitsune/settings_local.py`` file, but you don't have memcached running.

See :ref:`hacking-howto-memcached`.


Advanced install
================

The above covers a minimal install which will let you run most of
Kitsune. In order to get everything working, you'll need to install
some additional bits.

See the following chapters for installing those additional bits:

* Redis: :ref:`redis-chapter`
* RabbitMQ: :ref:`celery-chapter`
* Elastic Search: :ref:`search-chapter`
* Email: :ref:`email-chapter`

If you want to install Kitsune on an Apache server in a mod_wsgi
environment, see :ref:`wsgi-chapter`.
