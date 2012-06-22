========================================
Coding Conventions and Other Coding Info
========================================

This document contains useful information about our coding conventions, and
things to watch out for, etc.


Coding conventions
==================

We follow most of the practices as detailed in the `Mozilla webdev bootcamp
guide <http://mozweb.readthedocs.org/en/latest/coding.html>`_.


Git conventions
===============

See :ref:`patching` for our Git usage conventions.

See `Webdev bootcamp guide
<http://mozweb.readthedocs.org/en/latest/git.html#git-and-github>`_
for:

* git commit message conventions
* helpful resources for learning git
* helpful tools


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
