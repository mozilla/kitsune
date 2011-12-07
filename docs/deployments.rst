===================
Kitsune Deployments
===================


This documents the current development (dev), staging, production (prod), and
Continuous Integration (CI) servers for the ``support.mozilla.com`` instance of
`Kitsune <https://github.com/mozilla/kitsune>`_.

This document will not detail *how* Kitsune is deployed, only why, when, and
where.


The Source
==========

All of the source code for Kitsune lives in `a single Github repo
<https://github.com/mozilla/kitsune>`_. There are two important branches and we
use tags.


Branches
========


Master
------

The ``master`` branch is our main integration points. All new patches should be
based on the latest ``master`` (or rebased to it) and except for very rare
cases, all patches should land on ``master`` first. ``master`` never has code
freezes.

Our `dev server <https://support-dev.allizom.org/>`_ runs ``master``, and it
updates after every commit using a Github service hook.


Next
----

The ``next`` branch provides a stable place for QA to test and verify changes
before they go to production. Every week, ``next`` is wiped out and re-branched
off the latest ``master``.

Occasionally, patches need to land on ``next`` after this branch happens. They
should land on ``master`` first and then be cherry-picked (with
``git cherry-pick``) onto ``next``.

Our `staging server <https://support.allizom.org/>`_ runs ``next``, and
it is updated manually with a big red button.


Tags
====

Every week, we create a new tag for a release. The tags are the date the
release will go to production (e.g., the tag ``2011-08-23`` was pushed to prod
on 23 August 2011). Tags are created from the ``next`` branch.


Production
==========

`Production <https://support.mozilla.com>`_ runs the latest tagged version of
Kitsune. It is typically updated on Tuesday afternoons, Pacific Time.
Deployments to production are manually triggered.
