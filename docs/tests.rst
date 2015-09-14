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


In-Suite Selenium Tests
=======================

Front end testing that can't be done with Mocha can be done with
Selenium_, a system for remote-controlling real browser windows and
verifying behavior. Currently the tests are hard coded to use a local
instance of Firefox.

.. _Selenium: http://docs.seleniumhq.org/

These tests are designed to be run locally on development laptops and
locally on Jenkins. They are to provide some more security that we
aren't breaking things when we write new code, and should run before
commiting to master, just like any of our other in-suite tests. They are
not intended to replace the QA test suites that run against dev, stage,
and prod, and are not intended to beat on the site to find vulnerabilities.

You don't need a Selenium server to run these, and don't need to install
anything more than a modern version of Firefox, and the dependencies in
the requirements directory.

These tests use Django's `Live Server TestCase`_ class as a base, which
causes Django to run a real http server for some of it's tests, instead
of it's mocked http server that is used for most tests. This means it
will allocate a port and try to render pages like a real server would.
If static files are broken for you, these tests will likely fail as
well.

.. _`Live Server TestCase`: https://docs.djangoproject.com/en/1.4/topics/testing/#django.test.LiveServerTestCase


Running Selenium Tests
----------------------

By default, the Selenium tests will run as a part of the normal test
suite. When they run, a browser window will open and steal input for a
moment. You don't need to interact with it, and if all goes well, it
will close when the tests are complete. This cycle of open/test/close
may happen more than once each time you run the tests, as each TestCase
that uses Selenium will open it's own webdriver, which opens a browser
window.

When the Selenium tests kick off, Django starts an instance of the
server with ``DEBUG=False``. Because of this, you have to run these
two commands before running the tests::

    ./manage.py collectstatic
    ./manage.py compress_assets


Writing Selenium Tests
----------------------

To add a Selenium test, subclass ``kitsune.sumo.tests.SeleniumTestCase``.
instance of Selenium's webdriver will be automatically instantiated and
is available at ``self.webdriver``, and you can do things like
``self.webdriver.get(url)`` and
``self.webdriver.find_element_by_css_selector('div.baz')``. For more details
about how to work with Selenium, you can check out Selenium HQ's guide_.

.. _guide: http://docs.seleniumhq.org/docs/03_webdriver.jsp


XVFB and Selenium
-----------------

Because Selenium opens real browser windows, it can be kind of annoying
as windows open and steal focus and switch workspaces. Unfortunatly,
Firefox doesn't have a headless mode of operation, so we can't simply
turn off the UI. Luckily, there is a way to work around this fairly
easily on Linux, and with some effort on OSX.

Linux
~~~~~

Install XVFB_ and run the tests with it's xvfb-run binary. For example, if you
run tests like::

    ./manage.py test -s --noinput --logging-clear-handlers


You can switch to this to run with XVFB::

    xvfb-run ./manage.py test -s --noinput --logging-clear-handlers


This creates a virtual X session for Firefox to run in, and sets up all the
fiddly environment variables to get this working well. The tests will run as
normal, and no windows will open, if all is working right.

.. _XVFB: http://www.x.org/archive/current/doc/man/man1/Xvfb.1.xhtml

OSX
~~~

The same method can be used for OSX, but it requires some fiddliness.
The default version of Firefox for OSX does not use X as it's graphic's
backend, so by default XVFB can't help. You can however run an X11 enabled
version of OSX and a OSX version of XVFB. You can find more details
`here <http://afitnerd.com/2011/09/06/headless-browser-testing-on-mac/>`_.

.. Note::

   I don't use OSX, and that blog article is fairly out of date. If you
   find a way to get this working bettter or easier, or have better docs to
   share, please do!


Troubleshooting
---------------

**It says "Selenium unavailable."**

    This could mean that Selenium couldn't launch Firefox or can
    launch it, but can't connect to it.

    Selenium by default looks for Firefox in "the usual places".
    You can explicitly tell it which Firefox binary to use with
    the ``SELENIUM_FIREFOX_PATH`` setting.

    For example, in your ``settings_local.py`` file::

        SELENIUM_FIREFOX_PATH = '/usr/bin/firefox'

    I do this to make sure I'm using Firefox stable for tests
    rather than Firefox nightly.


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
    sumo.stage    runs on -stage
    sumo.prod     runs on -prod and is read-only (it doesn't change any data)
    ============  ===========================================================

There's a qatestbot in IRC. You can ask it to run the QA tests by::

    qatestbot build <test-suite>
