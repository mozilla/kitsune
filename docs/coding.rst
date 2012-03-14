========================================
Coding Conventions and Other Coding Info
========================================

This document contains useful information about our coding conventions, and
things to watch out for, etc.


Tests
=====

* Avoid naming test files ``test_utils.py``, since we use a library with the
  same name. Use ``test__utils.py`` instead.

* If you're expecting ``reverse`` to return locales in the URL, use
  ``LocalizingClient`` instead of the default client for the ``TestCase``
  class.

* Many models have "modelmakers" which are easier to work with for
  some kinds of tests than fixtures. For example,
  ``forums.tests.document`` is the model maker for
  ``forums.models.Document``.
