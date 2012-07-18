===========
Conventions
===========

This document contains coding conventions, and things to watch out
for, etc.


Coding conventions
==================

We follow most of the practices as detailed in the `Mozilla webdev
bootcamp guide
<http://mozweb.readthedocs.org/en/latest/coding.html>`_.

If you don't have an editor that checks PEP-8 issues and runs pyflakes
for you, it's worth setting it up. Use `check.py
<https://github.com/jbalogh/check>`_ because it's awesome.


Git conventions
===============

Git workflow
------------

See :ref:`patching` for how we use Git, branches and merging.


Git commit messages
-------------------

Git commit messages should have the following form::

    [bug xxxxxxx] Short summary

    Longer explanation with paragraphs and lists and all that where
    each line is under 72 characters.

    * bullet 1
    * bullet 2

    Etc. etc.


Summary line should be capitalized, short and shouldn't exceed 50
characters. Why? Because this is a convention many git tools take
advantage of.

If the commit relates to a bug, the bug should show up in the summary
line in brackets.

There should be a blank line between the summary and the rest of the
commit message. Lines shouldn't exceed 72 characters.

See `these guidelines
<http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_
for some more explanation.


Git resources and tools
-----------------------

See `Webdev bootcamp guide
<http://mozweb.readthedocs.org/en/latest/git.html#git-and-github>`_
for:

* helpful resources for learning git
* helpful tools
