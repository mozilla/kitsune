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
<https://github.com/mozilla/kitsune>`_.


Branches
========


Master
------

The ``master`` branch is our main integration points. All new patches should be
based on the latest ``master`` (or rebased to it).

Pull requests are created from those branches. Pull requests may be opened at
any time, including before any code has been written.

Pull requests get reviewed.

Once reviewed, the branch is merged into ``master``, except in special cases
such as changes that require re-indexing. See
:ref:`Changes that involve reindexing <changes_reindexing>`.

We deploy to production from ``master``.


Dev
===

Dev is a small environment that is updated manually. We use it primarily to
develop infrastructure changes, like upgrading to Python 2.7.


Stage
=====

We deploy to stage anything we want to test including deployments themselves.
We deploy using the big red button. Typically we deploy to stage from master,
but we can deploy from any rev-ish thing.


Production
==========

We deploy to production from master by specified revisions. We deploy when
things are ready to go using the big red button.
