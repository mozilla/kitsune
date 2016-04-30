.. _tests-chapter:

=================
All about testing
=================

Kitsune has a fairly comprehensive Python test suite. Changes should
not break tests---only change a test if there is a good reason to
change the expected behavior---and new code should come with tests.


Running the Test Suite
======================

If you followed the steps in :ref:`the installation docs
<hacking-howto-chapter>`, then you should be all set setup-wise.

To run the tests, you need to do::

    ./manage.py test


That doesn't provide the most sensible defaults for running the
tests. Here is a good command to alias to something short::

    ./manage.py test -s --noinput --logging-clear-handlers


The ``-s`` flag is important if you want to be able to drop into PDB from
within tests.

Some other helpful flags are:

``-x``:
  Fast fail. Exit immediately on failure. No need to run the whole test suite
  if you already know something is broken.
``--pdb``:
  Drop into PDB on an uncaught exception. (These show up as ``E`` or errors in
  the test results, not ``F`` or failures.)
``--pdb-fail``:
  Drop into PDB on a test failure. This usually drops you right at the
  assertion.
``--no-skip``:
  All SkipTests show up as errors. This is handy when things shouldn't be
  skipping silently with reckless abandon.


Running a Subset of Tests
-------------------------

You can run part of the test suite by specifying the apps you want to run,
like::

    ./manage.py test kitsune/wiki kitsune/search kitsune/kbforums

You can also specify modules::

    ./manage.py test kitsune.wiki.tests.test_views

You can specify specific tests::

    ./manage.py test kitsune.wiki.tests.test_views:VersionGroupTests.test_version_groups

See the output of ``./manage.py test --help`` for more arguments.


Running tests without collecting static files
---------------------------------------------

By default the test runner will run ``collectstatic`` to ensure that all the required assets have
been collected to the static folder. If you do not want this default behavior you can run::

    REUSE_STATIC=1 ./manage.py test


The Test Database
-----------------

The test suite will create a new database named ``test_%s`` where
``%s`` is whatever value you have for
``settings.DATABASES['default']['NAME']``.

Make sure the user has ``ALL`` on the test database as well. This is
covered in the installation chapter.

When the schema changes, you may need to drop the test database. You
can also run the test suite with ``FORCE_DB`` once to cause Django to
drop and recreate it::

    FORCE_DB=1 ./manage.py test -s --noinput --logging-clear-handlers


Writing New Tests
=================

Code should be written so it can be tested, and then there should be
tests for it.

When adding code to an app, tests should be added in that app that
cover the new functionality. All apps have a ``tests`` module where
tests should go. They will be discovered automatically by the test
runner as long as the look like a test.

* If you're expecting ``reverse`` to return locales in the URL, use
  ``LocalizingClient`` instead of the default client for the
  ``TestCase`` class.

* We use "modelmakers" instead of fixtures. Models should have
  modelmakers defined in the tests module of the Django app. For
  example, ``forums.tests.document`` is the modelmaker for
  ``forums.Models.Document`` class.


Changing Tests
==============

Unless the current behavior, and thus the test that verifies that
behavior is correct, is demonstrably wrong, don't change tests. Tests
may be refactored as long as its clear that the result is the same.


Removing Tests
==============

On those rare, wonderful occasions when we get to remove code, we
should remove the tests for it, as well.

If we liberate some functionality into a new package, the tests for
that functionality should move to that package, too.


JavaScript Tests
================

Frontend JavaScript is currently tested with Mocha_.


Running JavaScript Tests
------------------------

To run tests, make sure you have have the NPM dependencies installed, and
then run::

  $ scripts/mocha.sh

Writing JavaScript Tests
------------------------

Mocha tests are discovered using the pattern
``kitsune/*/static/*/js/tests/**/*.js``. That means that any app can
have a `tests` directory in its JavaScript directory, and the files in
there will all be considered test files. Files that don't define tests
won't cause issues, so it is safe to put testing utilities in these
directories as well.


Here are a few tips for writing tests:

* Any HTML required for your test should be added by the tests or a
  ``beforeEach`` function in that test suite. React is useful for this.
* You can use `sinon` to mock out parts of libraries or functions under
  test. This is useful for testing AJAX.
* The tests run in a Node.js environment. A browser environment can be
  simulated using ``jsdom``. Specifically, ``mocha-jsdom`` is useful to
  set up and tear down the simulated environment.

.. _Mocha: https://mochajs.org/


Functional UI Tests
===================

We can do more comprehensive front-end testing with the functional UI tests.
They're located in the ``tests/functional`` directory.

Installing dependencies
-----------------------

Follow the steps in :ref:`the installation docs <hacking-howto-chapter>`,
including the test dependencies to make sure you have everything you need to
run the tests. If you're running the tests against a deployed environment then
there's no need to install anything other than the test dependencies.

Create test users
-----------------

Some of the tests require logging in as a administrator, and others require
logging in as a user. To run these tests you will need to create accounts in
the target environment. If you're running against a local instance of the
application you can create these users by running the following script::

  $ ./manage.py shell < ./scripts/create_user_and_superuser.py

If you want to run the tests that require administrator access against a
deployed instance, then you will need to ask someone on IRC to upgrade one of
your test accounts.

The credentials associated with the test users are stored in a JSON file, which
we then pass to the tests via the command line. If you used the above mentioned
script, then these users are stored in ``/scripts/travis/variables.json``. The
variable file needs to be referenced on the command line when running the
tests.

The following is an example JSON file with the values missing. You can use this
as a template:

.. code:: json

   {
     "users": {
       "default": {
         "username": "",
         "password": "",
         "email": ""},
       "admin": {
         "username": "",
         "password": "",
         "email": ""}
     }
   }

For the purposes of the examples below, assume you named your copy of the file
``my_variables.json``.

Running the tests
-----------------

Tests are run using the command line. Below are a couple of examples of running
the tests:

To run all of the desktop tests against the default environment::

  $ py.test --driver Firefox --variables my_variables.json tests/functional/desktop

To run against a different environment, pass in a value for ``--base-url``,
like so::

  $ py.test --base-url https://support.allizom.org --driver Firefox --variables my_variables.json tests/functional/desktop

To run the mobile tests you will need to target a mobile device or emulator
using a tool like `Appium <http://appium.io/>`_::

  $ py.test --driver Remote --port 4723 \
  --capability platformName iOS \
  --capability platformVersion 9.2 \
  --capability deviceName "iPhone 6" \
  --capability browserName Safari \
  --variables my_variables.json \
  tests/functional/mobile

Alternatively, if you run the mobile tests in Firefox the user agent will be
changed to masquerade as a mobile browser.

The pytest plugin that we use for running tests has a number of advanced
command line options available. To see the options available, run
``py.test --help``. The full documentation for the plugin can be found
`here <https://pytest-selenium.readthedocs.io/>`_.
