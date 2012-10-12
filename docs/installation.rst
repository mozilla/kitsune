.. _installation-chapter:

============
Installation
============

Requirements
============

To run everything and make all the tests pass locally, you'll need the
following things (in addition to Git, of course).

* Python 2.6 or 2.7.

* `setuptools <http://pypi.python.org/pypi/setuptools#downloads>`_
  or `pip <http://pip.openplans.org/>`_.

* MySQL Server and client headers.

* Memcached Server.

* RabbitMQ.

* ``libxml`` and headers.

* ``libxslt`` and headers.

* ``libjpeg`` and headers.

* ``zlib`` and headers.

* LESS

* `Redis <http://redis.io>`_

* Several Python packages. See `Installing the Packages`_.

* Elastic Search. :ref:`search-chapter` covers installation,
  configuration, and running.

Installation for these is very system dependent. Using a package manager, like
yum, aptitude, or brew, is encouraged.


Additional Requirements
-----------------------

If you want to use Apache, instead of the dev server (not strictly required but
it's more like our production environment) you'll also need:

* Apache HTTPD Server.

* ``mod_wsgi``

See the documentation on :ref:`WSGI <wsgi-chapter>` for more
information and instructions.


Getting the Source
==================

Grab the source from Github using::

    $ git clone --recursive git://github.com/mozilla/kitsune.git
    $ cd kitsune

If you forgot to add ``--recursive``, you can get all the submodules with::

    $ git submodule update --init --recursive


Installing the Packages
=======================

Compiled Packages
-----------------

There are a small number of compiled packages, including the MySQL Python
client. You can install these using ``pip`` (if you don't have ``pip``, you
can get it with ``easy_install pip``) or via a package manager.
To use ``pip``, you only need to do this::

    $ sudo pip install -r requirements/compiled.txt


Python Packages
---------------

All the pure-Python requirements are provided in the ``vendor`` directory, also
known as the "vendor library". This makes the packages available to Python
without installing them globally and keeps them pinned to known-compatible
versions.

See the :ref:`vendor library <vendor-chapter>` documentation for more
information on getting the vendor lib and keeping it up to date.


Configuration
=============

Start by creating a file named ``settings_local.py`` in the kitsune
directory, and putting this line in it::

    from settings import *

Now you can copy and modify any settings from ``settings.py`` into
``settings_local.py`` and the value will override the default.

For local development you will want to add the following settings::

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
            'PASSWORD': '<YOUR_PASSWORD>',
            'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
            'TEST_CHARSET': 'utf8',
            'TEST_COLLATION': 'utf8_unicode_ci',
            },
        }

    REDIS_BACKENDS = {
            'default': 'redis://localhost:6379?socket_timeout=0.5&db=0',
            'karma': 'redis://localhost:6381?socket_timeout=0.5&db=0',
            'helpfulvotes': 'redis://localhost:6379?socket_timeout=0.\
                5&db=1',
        }

    REDIS_BACKEND = REDIS_BACKENDS['default']

    LESS_PREPROCESS = True


Redis
-----

You need to copy the ``REDIS_BACKEND`` section from ``settings.py``
into your ``settings_local.py``.  After doing that, uncomment the
three lines in each section.

There are three ``.conf`` files in ``configs/redis/``.  One is for
testing and is used in ``settings_test.py``.  The other two are used
for the sections in ``REDIS_BACKEND``.

There are two ways to set this up.  First is to set it up like in
``settings.py`` and run all three redis servers.  The second is to set
it up differently, tweak the settings in ``settings_local.py``
accordingly, and run Redis using just the test configuration.


memcache
--------

.. Note::

   This should probably be somewhere else, but the easy way to flush
   your cache is something like this::

       echo "flush_all" | nc localhost 11211

   Assuming you have memcache configured to listen to 11211.


Database
--------

At a minimum, you will need to define a database connection. An example
configuration is::

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

Note the two settings ``TEST_CHARSET`` and ``TEST_COLLATION``. Without these,
the test suite will use MySQL's (moronic) defaults when creating the test
database (see below) and lots of tests will fail. Hundreds.

Create the database and grant permissions to the user, based on your database
settings. For example, using the settings above::

    $ mysql -u root -p
    mysql> CREATE DATABASE kitsune;
    mysql> GRANT ALL ON kitsune.* TO kitsune@localhost IDENTIFIED BY \
        'password';

To load the latest database schema, use ``scripts/schema.sql`` and
``schematic``::

    $ mysql -u kitsune -p kitsune < scripts/schema.sql
    $ ./vendor/src/schematic/schematic migrations/

You'll now have an empty but up-to-date database!

Finally, you'll probably want to create a superuser. Just use Django's
``createsuperuser`` management command::

    $ ./manage.py createsuperuser

And follow the prompts. After logging in, you can create a profile for the
user by going to ``/users/edit`` in your browser.

See also the :ref:`important wiki documents <wiki-chapter>` documentation.


Product Details Initialization
------------------------------

One of the packages Kitsune uses, ``product_details``, needs to fetch JSON
files containing historical Firefox version data and write them within its
package directory. To set this up, run this command to do the initial fetch::

    $ ./manage.py update_product_details


LESS
----

To install LESS you will first need to `install Node.js and NPM
<https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager>`_.

Now install LESS using::

    $ sudo npm install less

Ensure that lessc (might be located at /usr/lib/node_modules/less/bin) is
accessible on your PATH.


Running redis
-------------

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


Elastic search
--------------

Elastic Search. :ref:`search-chapter` covers installation,
configuration, and running.

.. todo:: The installation side of these two should get moved here.


Testing it Out
==============

To start the dev server, run ``./manage.py runserver``, then open up
``http://localhost:8000``. If everything's working, you should see a somewhat
empty version of the SUMO home page!


Running the Tests
-----------------

A great way to check that everything really is working is to run the test
suite. You'll need to add an extra grant in MySQL for your database user::

    GRANT ALL ON test_NAME.* TO USER@localhost;

Where ``NAME`` and ``USER`` are the same as the values in your database
configuration.

The test suite will create and use this database, to keep any data in your
development database safe from tests.

Running the test suite is easy::

    $ ./manage.py test -s --noinput --logging-clear-handlers

For more information, see the :ref:`test documentation <tests-chapter>`.

.. Note::

   Some of us use `nose-progressive
   <https://github.com/erikrose/nose-progressive>`_ because it makes
   tests easier to run and debug.
