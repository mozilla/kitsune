.. _tests-chapter:

=================
All about testing
=================

Kitsune has a fairly comprehensive Python test suite. Changes should not break
tests---only change a test if there is a good reason to change the expected
behavior---and new code should come with tests.


Running the Test Suite
======================

If you followed the steps in :ref:`the installation docs
<hacking-howto-chapter>`, then all you should need to do to run the
test suite is::

    ./manage.py test


However, that doesn't provide the most sensible defaults. Here is a good
command to alias to something short::

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


Running a Subset of Tests
-------------------------

You can run part of the test suite by specifying the apps you want to run,
like::

    ./manage.py test wiki search kbforums

You can also specify modules::

    ./manage.py test wiki.tests.test_views

You can specify specific tests::

    ./manage.py test wiki.tests.test_views:VersionGroupTests.test_version_groups

You can also exclude tests that match a regular expression with ``-e``::

    ./manage.py test -e"search"

See the output of ``./manage.py test --help`` for more arguments.


The Test Database
-----------------

The test suite will create a new database named ``test_%s`` where ``%s`` is
whatever value you have for ``settings.DATABASES['default']['NAME']``.

Make sure the user has ``ALL`` on the test database as well. This is
covered in the installation chapter.

When the schema changes, you may need to drop the test database. You can also
run the test suite with ``FORCE_DB`` once to cause Django to drop and recreate
it::

    FORCE_DB=1 ./manage.py test -s --noinput --logging-clear-handlers


Writing New Tests
=================

Code should be written so it can be tested, and then there should be tests for
it.

When adding code to an app, tests should be added in that app that cover the
new functionality. All apps have a ``tests`` module where tests should go. They
will be discovered automatically by the test runner as long as the look like a
test.

* Avoid naming test files ``test_utils.py``, since we use a library
  with the same name. Use ``test__utils.py`` instead.

* If you're expecting ``reverse`` to return locales in the URL, use
  ``LocalizingClient`` instead of the default client for the
  ``TestCase`` class.

* Many models have "modelmakers" which are easier to work with for
  some kinds of tests than fixtures. For example,
  ``forums.tests.document`` is the model maker for
  ``forums.models.Document``.


Changing Tests
==============

Unless the current behavior, and thus the test that verifies that behavior is
correct, is demonstrably wrong, don't change tests. Tests may be refactored as
long as its clear that the result is the same.


Removing Tests
==============

On those rare, wonderful occasions when we get to remove code, we should remove
the tests for it, as well.

If we liberate some functionality into a new package, the tests for that
functionality should move to that package, too.


JavaScript Tests
================

Frontend JavaScript is currently tested with QUnit_, a simple set of
functions for test setup/teardown and assertions.


Running JavaScript Tests
------------------------

You can run the tests a few different ways but during development you
probably want to run them in a web browser by opening this page:
http://127.0.0.1:8000/en-US/qunit/

Before you can load that page, you'll need to adjust your
``kitsune/settings_local.py`` file so it includes django-qunit::

    INSTALLED_APPS += (
        # ...
        'django_qunit',
    )


Writing JavaScript Tests
------------------------

QUnit_ tests for the HTML page above are discovered automatically.  Just add
some_test.js to ``media/js/tests/`` and it will run in the suite.  If
you need to include a library file to test against, edit
``media/js/tests/suite.json``.

QUnit_ has some good examples for writing tests.  Here are a few
additional tips:

* Any HTML required for your test should go in a sandbox using
  ``tests.createSandbox('#your-template')``.
  See js/testutils.js for details.
* To make a useful test based on an actual production template, you can create
  a snippet and include that in ``templates/tests/qunit.html`` assigned to its own
  div.  During test setup, reference the div in createSandbox()
* You can use `$.mockjax`_ to test how your code handles server responses,
  errors, and timeouts.

.. _Qunit: http://docs.jquery.com/Qunit
.. _`$.mockjax`: http://enterprisejquery.com/2010/07/mock-your-ajax-requests-with-mockjax-for-rapid-development/


.. _tests-chapter-qa-test-suite:

The QA test suite
=================

QA has their own test suite. The code is located on github at
`<https://github.com/mozilla/sumo-tests/>`_.

There are three test suites. They differ in what they do and where
they run:

    ============  ===========================================================
    name          description
    ============  ===========================================================
    sumo.fft      runs on -dev
    sumo.release  runs on -stage
    sumo.prod     runs on -prod and is read-only (it doesn't change any data)
    ============  ===========================================================

There's a qatestbot in IRC. You can ask it to run the QA tests by::

    qatestbot build <test-suite>
