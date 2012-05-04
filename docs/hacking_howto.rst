.. _hacking-howto-chapter:

==============================
Hacking Howto for Contributors
==============================


Summary
=======

This chapter helps you get a minimal installation of Kitsune up and
running so as to make it easier for contributing.

If you're interested in setting up Kitsune for a production
deployment, this is not the chapter for you---look no further!

If you have any problems getting Kitsune running, let us know. See the
:ref:`contact-us-chapter`.


Requirements
============

You'll need the following:

* git
* Python 2.6
* `pip <http://pip.openplans.org/>`_
* MySQL server and client headers
* Memcached Server
* libxml and headers
* libxslt and headers
* libjpeg and headers
* zlib and headers
* `RabbitMQ <http://www.rabbitmq.com/>`_
* `Redis <http://redis.io>`_

Installation for these is very system dependent. Using a package
manager, like yum, aptitude, or brew, is encouraged.

.. Note::

   Make sure you have ``python26`` in your path.  If not, create a
   symbollic link for it::

       $ ln -s /usr/bin/python /usr/bin/python26

   Or something along those lines depending on how your system is set
   up.


Getting the Source
==================

Grab the source from Github using::

    $ git clone --recursive git://github.com/mozilla/kitsune.git
    $ cd kitsune

.. Note::

   If you forgot to add ``--recursive``, you can get all the
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
    CELERY_ALWAYS_EAGER = False

    # Allows you to specify waffle settings in the querystring.
    WAFFLE_OVERRIDE = True

    # Change this to True if you're going to be doing search-related
    # work.
    ES_LIVE_INDEXING = False

    # Basic cache configuration for development.
    CACHES = {
        'default': {
            'BACKEND': 'caching.backends.memcached.CacheClass',
            'LOCATION': 'localhost:11211'
            }
        }

    CACHE_BACKEND = 'caching.backends.memcached://localhost:11211'
    CACHE_MACHINE_USE_REDIS = True
    CACHE_MIDDLEWARE_ALIAS = 'default'
    CACHE_MIDDLEWARE_KEY_PREFIX = ''
    CACHE_MIDDLEWARE_SECONDS = 600
    CACHE_PREFIX = 'sumo:'

    # Basic database configuration for development.
    DATABASES = {
        'default': {
            'NAME': 'kitsune',
            'ENGINE': 'django.db.backends.mysql',
            'HOST': 'localhost',
            'USER': 'kitsune',
            'PASSWORD': 'password',
            'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
            'TEST_CHARSET': 'utf8',
            'TEST_COLLATION': 'utf8_unicode_ci',
            },
        }

Now you can copy and modify any settings from ``settings.py`` into
``settings_local.py`` and the value will override the default.


Redis
-----

FIXME - do we need redis in the minimal install?

You need to copy the ``REDIS_BACKEND`` section from ``settings.py``
into your ``settings_local.py``.  After doing that, uncomment the
three lines in each section.

There are three ``.conf`` files in ``config/redis/``.  One is for
testing and is used in ``settings_test.py``.  The other two are used
for the sections in ``REDIS_BACKEND``.

There are two ways to set this up.  First is to set it up like in
``settings.py`` and run all three redis servers.  The second is to set
it up differently, tweak the settings in ``settings_local.py``
accordingly, and run Redis using just the test configuration.


memcache
--------

FIXME - do we need memcache in the minimal install?

.. Note::

   This should probably be somewhere else, but the easy way to flush
   your cache is something like this::

       echo "flush_all" | nc localhost 11211

   Assuming you have memcache configured to listen to 11211.


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

    $ mysql -uroot -p
    mysql> CREATE DATABASE kitsune;
    mysql> GRANT ALL ON kitsune.* TO kitsune@localhost IDENTIFIED BY \
        'password';

To load the latest database schema, use ``scripts/schema.sql`` and
``schematic``::

    $ mysql kitsune < scripts/schema.sql
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


Running redis
-------------

FIXME - do we need redis in the minimal install?

This script runs all three servers---one for each configuration.

I (Will) put that in a script that creates the needed directories in
``/var/redis/`` and kicks off the three redis servers::

    #!/bin/bash

    set -e

    # Adjust these according to your setup!
    REDISBIN=/usr/bin/redis-server
    CONFFILE=/path/to/conf/files/

    if test ! -e /var/redis/sumo/
    then
        echo "creating /var/redis/sumo/"
        mkdir -p /var/redis/sumo/
    fi

    if test ! -e /var/redis/sumo-test/
    then
        echo "creating /var/redis/sumo-test/"
        mkdir -p /var/redis/sumo-test/
    fi

    if test ! -e /var/redis/sumo-persistent/
    then
        echo "creating /var/redis/sumo-persistent/"
        mkdir -p /var/redis/sumo-persistent/
    fi

    $REDISBIN $CONFFILE/redis-persistent.conf
    $REDISBIN $CONFFILE/redis-test.conf
    $REDISBIN $CONFFILE/redis-volatile.conf


Testing it out
==============

To start the dev server, run ``./manage.py runserver``, then open up
``http://localhost:8000``.

If everything's working, you should see a somewhat empty version of
the SUMO home page!


Running the tests
-----------------

A great way to check that everything really is working is to run the
test suite. You'll need to add an extra grant in MySQL for your
database user::

    GRANT ALL ON test_NAME.* TO USER@localhost;

Where ``NAME`` and ``USER`` are the same as the values in your
database configuration.

The test suite will create and use this database, to keep any data in
your development database safe from tests.

Running the test suite is easy::

    $ ./manage.py test -s --noinput --logging-clear-handlers

For more information, see the :ref:`test documentation
<tests-chapter>`.
