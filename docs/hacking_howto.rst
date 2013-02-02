.. _hacking-howto-chapter:

==============================
Hacking HOWTO for Contributors
==============================

.. contents::
   :local:


Summary
=======

This chapter helps you get a minimal installation of Kitsune up and
running so as to make it easier for contributing.

If you're setting Kitsune up for deployment, make sure you read all
the way to the end and then read the additional sections.

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

We know these work in Debian Testing (Wheezy) and Ubuntu 12.04 and
will probably work in other distributions. It's likely that you'll
encounter some steps that are slightly different. If you run into
problems, let us know.


Requirements
============

These are required for the minimum installation:

* git
* Python 2.6 or 2.7
* pip: `<http://www.pip-installer.org/en/latest/>`_
* MySQL server and client headers
* Memcached Server
* libxml and headers
* libxslt and headers
* libjpeg and headers
* zlib and headers

These are optional:

* Redis
* LESS
* ElasticSearch: :ref:`search-chapter`

Installation for these is very system dependent. Using a package
manager, like yum, aptitude, or brew, is encouraged.


Getting the Source
==================

Grab the source from Github using::

    $ git clone --recursive git://github.com/mozilla/kitsune.git
    $ cd kitsune

.. Note::

   If you forgot to add ``--recursive``, you can still get all the
   submodules with::

       $ git submodule update --init --recursive


Installing dependencies
=======================

Compiled Packages
-----------------

There are a small number of compiled packages, including the MySQL
Python client.

You can install these either with your system's package manager or
with ``pip``.

To use pip, do this::

    $ sudo pip install -r requirements/compiled.txt

If you want to use your system's package manager, you'll need to go
through ``requirements/compiled.txt`` and install the dependencies by
hand.


Python Packages
---------------

All the pure-Python requirements are provided in the ``vendor``
directory, also known as the "vendor library". This makes the packages
available to Python without installing them globally and keeps them
pinned to known-compatible versions.

See the :ref:`vendor library <vendor-chapter>` documentation for more
information on getting the vendor lib and keeping it up to date.


Configuration
=============

Start by creating a file named ``settings_local.py`` in the
``kitsune`` directory. Start with this::

    from settings import *

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

Don't forget to change ``<YOUR_PASSWORD>``!

Now you can copy and modify any settings from ``settings.py`` into
``settings_local.py`` and the value will override the default.


memcached
---------

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


LESS
----

To install LESS you will first need to `install Node.js and NPM
<https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager>`_.

Now install LESS using::

    $ npm install less

Ensure that `LESS_BIN` was configured correctly in your local
settings.

.. note:: If you see empty CSS files when you are running the
   dev server, you have to remove all empty files having a
   ``.less.css`` since they are empty and should be regenerated.

   To do this, run the following command on the top directory
   of your Kitsune clone::

       $ rm **/*.less.css

   and *hard-refresh* your pages on the browser via *Ctrl + Shift + R*.


Database
--------

At a minimum, you will need to define a database connection. See above
for a sample database configuration.

Note the two settings ``TEST_CHARSET`` and ``TEST_COLLATION``. Without
these, the test suite will use MySQL's (moronic) defaults when
creating the test database (see below) and lots of tests will
fail. Hundreds.

Create the database and grant permissions to the user, based on your
database settings. For example, using the settings above::

    $ mysql -u root -p
    mysql> CREATE DATABASE kitsune;
    mysql> GRANT ALL ON kitsune.* TO kitsune@localhost IDENTIFIED BY '<YOUR_PASSWORD>';

To load the latest database schema, use ``scripts/schema.sql`` and
``schematic``::

    $ mysql -u kitsune -p kitsune < scripts/schema.sql
    $ ./vendor/src/schematic/schematic migrations/

You'll now have an empty but up-to-date database!

Finally, you'll probably want to create a superuser. Just use Django's
``createsuperuser`` management command::

    $ ./manage.py createsuperuser

and follow the prompts. After logging in, you can create a profile for
the user by going to ``/users/edit`` in your browser.

See also the :ref:`important wiki documents <wiki-chapter>`
documentation.


Product Details Initialization
------------------------------

One of the packages Kitsune uses, ``product_details``, needs to fetch
JSON files containing historical Firefox version data and write them
within its package directory. To set this up, run this command to do
the initial fetch::

    $ ./manage.py update_product_details


Install Sample Data
-------------------

We include some sample data to get you started. You can install it by
running this command::

    $ ./manage.py generatedata


Testing it out
==============

To start the dev server, run ``./manage.py runserver``, then open up
``http://localhost:8000``.

If everything's working, you should see a somewhat empty version of
the SUMO home page!


Setting it up
-------------

A great way to check that everything really is working is to run the
test suite. You'll need to add an extra grant in MySQL for your
database user::

    $ mysql -u root -p
    mysql> GRANT ALL ON test_NAME.* TO USER@localhost;

Where ``NAME`` and ``USER`` are the same as the values in your
database configuration.

The test suite will create and use this database, to keep any data in
your development database safe from tests.


Running the tests
-----------------

Running the test suite is easy::

    $ ./manage.py test -s --noinput --logging-clear-handlers

For more information, see the :ref:`test documentation
<tests-chapter>`.


Advanced install
================

The above covers a minimal install which will let you run most of
Kitsune. In order to get everything working, you'll need to install
some additional bits.

See the following chapters for installing those additional bits:

* Redis: :ref:`redis-chapter`
* RabbitMQ: :ref:`celery-chapter`
* Elastic Search: :ref:`search-chapter`

If you want to install Kitsune on an Apache server in a mod_wsgi
environment, see :ref:`wsgi-chapter`.
