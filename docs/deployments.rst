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
based on the latest ``master`` (or rebased to it).

Pull requests are created from those branches when they're "done".

Pull requests get reviewed.

Once reviewed, the branch is rebased against ``master`` and then landed on
``master``.

Our `dev server <https://support-dev.allizom.org/>`_ runs ``master``, and it
updates every 15 minutes via a cron job.

We deploy to production from ``master``.


Dev
===

Dev runs whatever is in master and updates on every commit via github hooks
to an updater script.


Stage
=====

We deploy to stage anything we want to test including deployments themselves.
We deploy using the big red button. Typically we deploy to stage from master,
but we can deploy from any rev-ish thing.


Production
==========

We deploy to production from master by specified revisions. We deploy when
things are ready to go using the big red button.
