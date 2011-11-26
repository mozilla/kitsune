.. _installation-chapter:

============
Installation
============

Requirements
============

To run everything and make all the tests pass locally, you'll need the
following things (in addition to Git, of course).

* Python 2.6.

* `setuptools <http://pypi.python.org/pypi/setuptools#downloads>`_
  or `pip <http://pip.openplans.org/>`_.

* MySQL Server and client headers.

* Memcached Server.

* `Sphinx <http://sphinxsearch.com/>`_ 0.9.9, compiled with the
  ``--enable-id64`` flag.

* RabbitMQ.

* ``libxml`` and headers.

* ``libxslt`` and headers.

* ``libjpeg`` and headers.

* ``zlib`` and headers.

* `Redis <http://redis.io>`_

* Several Python packages. See `Installing the Packages`_.

Installation for these is very system dependent. Using a package manager, like
yum, aptitude, or brew, is encouraged.


.. Note::

   Make sure you have ``python26`` in your path.  If not, create a
   symbollic link for it::

       ln -s /usr/bin/python /usr/bin/python26

   Or something along those lines depending on how your system is set up.


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

    $ git clone --recursive git://github.com/jsocol/kitsune.git
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

Redis
-----

You need to copy the ``REDIS_BACKEND`` and ``REDIS_TEST_BACKEND``
sections from ``settings.py`` into your ``settings_local.py``.  After
doing that, uncomment the three lines in each section.

There are three ``.conf`` files in ``config/redis/`` each
corresponding to a different redis server configuration.  You need to
run all three redis servers.

The three conf files need to match the settings in ``settings_local.py``.


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
            'PASSWORD': 'password',
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

And follow the prompts. After logging in, you can create a profile for the
user by going to ``/users/edit`` in your browser.

See also the :ref:`important wiki documents <wiki-chapter>` documentation.


Product Details Initialization
------------------------------

One of the packages Kitsune uses, ``product_details``, needs to fetch JSON
files containing historical Firefox version data and write them within its
package directory. To set this up, run this command to do the initial fetch::

    $ ./manage.py update_product_details


Running redis
-------------

You'll need to run three redis servers--one for each configuration.

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


Setting Up Search
=================

See the :ref:`search documentation <search-chapter>` for steps to get
Sphinx search working.
