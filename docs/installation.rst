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

* Several Python packages. See `Installing the Packages`_.

Installation for these is very system dependent. Using a package manager, like
yum, aptitude, or brew, is encouraged.


Additional Requirements
-----------------------

If you want to use Apache, instead of the dev server (not strictly required but
it's more like our production environment) you'll also need:

* Apache HTTPD Server.

* ``mod_wsgi``

See the documentation on `WSGI <wsgi.rst>`_ for more information and
instructions.


Getting the Source
==================

Grab the source from Github using::

    git clone --recursive git://github.com/jsocol/kitsune.git
    cd kitsune


Installing the Packages
=======================

Compiled Packages
-----------------

There are a small number of compiled packages, including the MySQL Python
client. You can install these using ``pip`` (if you don't have ``pip``, you
can get it with ``easy_install pip``) or via a package manager.
To use ``pip``, you only need to do this::

    sudo pip install -r requirements/compiled.txt


Python Packages
---------------

All of the pure-Python requirements are available in a git repository, known as
a vendor library. This allows them to be available on the Python path without
needing to be installed in the system, allowing multiple versions for multiple
projects simultaneously.

The vendor library is a submodule in ``vendor/``. If you clone Kitsune with
``--recursive`` above, you should have everything, but to be safe, or when the
vendor submodule changes, you should run this::

    cd vendor
    git submodule update --init --recursive
    cd ..


Configuration
=============

Start by creating a file named ``settings_local.py``, and putting this line in
it::

    from settings import *

Now you can copy and modify any settings from ``settings.py`` into
``settings_local.py`` and the value will override the default.


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

See also the `important wiki documents <wikidocs.rst>`_ documentation.


Product Details Initialization
------------------------------

One of the packages Kitsune uses, ``product_details``, needs to fetch JSON
files containing historical Firefox version data and write them within its
package directory. To set this up, run this command to do the initial fetch::

    $ ./manage.py update_product_details


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

    ./manage.py test -s --noinput --logging-clear-handlers

For more information, see the `test documentation <tests.rst>`_.


Setting Up Search
=================

See the `search documentation <search.rst>`_ for steps to get Sphinx search
working.
