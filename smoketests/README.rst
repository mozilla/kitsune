==================
Kitsune smoketests
==================

This directory holds Kitsune client-based smoke tests. We use the same
infrastructure that `Fjord uses <https://github.com/mozilla/fjord/>`_.

These tests use the following things:

1. py.test
2. pytest-mozwebqa
3. pytest-xdist
4. selenium


Setting up to run the tests
===========================

I suggest using a different virtual environment for these tests than the
rest of Kitsune so you're not mixing requirements. The requirements are
listed in requirements.txt.


Running the tests
=================

Whenever you want to run these tests, first enter your virtual environment.

To run tests it's a simple case of calling ``py.test`` from the root
directory::

    $ py.test --driver=firefox tests


.. Note::

   When giving a baseurl, make sure it doesn't have a ``/`` at the end.


For more command line options see https://github.com/davehunt/pytest-mozwebqa


Running tests against localhost
-------------------------------

Running tests against a local instance of Kitsune::

    $ py.test --driver=firefox --baseurl=http://localhost:8000 tests


Running tests on stage
----------------------

Running tests against the SUMO stage environment::

    $ py.test --driver=firefox --baseurl=https://support.allizom.org tests


.. Note::

   Some of the dashboard tests may fail depending on what data is on
   stage.


Running specific tests
----------------------

You can run tests in a given file::

    $ py.test tests/desktop/test_search.py


Running tests with xvfb
-----------------------

Because Selenium opens real browser windows, it can be kind of
annoying as windows open and steal focus and switch
workspaces. Unfortunatly, Firefox doesn't have a headless mode of
operation, so we can't simply turn off the UI. Luckily, there is a way
to work around this fairly easily on Linux, and with some effort on
OSX.


On Linux:

    Install Xvfb and run the tests with it's xvfb-run binary. For
    example, if you run tests like::

        $ py.test ...


    You can switch to this to run with Xvfb::

        $ xvfb-run py.test ...


    This creates a virtual X session for Firefox to run in, and sets
    up all the fiddly environment variables to get this working
    well. The tests will run as normal, and no windows will open, if
    all is working right.


On OSX:

    The same method can be used for OSX, but it requires some
    fiddliness.  The default version of Firefox for OSX does not use X
    as it's graphic's backend, so by default Xvfb can't help. You can
    however run an X11 enabled version of OSX and a OSX version of
    Xvfb. You can find more details `here
    <http://afitnerd.com/2011/09/06/headless-browser-testing-on-mac/>`_.

    .. Note::

       I don't use OSX, and that blog article is fairly out of
       date. If you find a way to get this working bettter or easier,
       or have better docs to share, please do!


Writing Tests
=============

If you want to get involved and add more tests then there's just a few
things we'd like to ask you to do:

1. Use the Mozilla WebQA `template files`_ for all new tests and page objects
2. Follow the Mozilla WebQA `style guide`_
3. Fork this project with your own GitHub account
4. Make sure all tests are passing, and submit a pull request with your changes

.. _template files: https://github.com/mozilla/mozwebqa-test-templates
.. _style guide: https://wiki.mozilla.org/QA/Execution/Web_Testing/Docs/Automation/StyleGuide


License
=======

This software is licensed under the `MPL`_ 2.0:

    This Source Code Form is subject to the terms of the Mozilla Public
    License, v. 2.0. If a copy of the MPL was not distributed with this
    file, You can obtain one at http://mozilla.org/MPL/2.0/.

.. _MPL: http://www.mozilla.org/MPL/2.0/
