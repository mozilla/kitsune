.. _celery-chapter:

=================
Celery and Redis
=================

Kitsune uses `Celery <http://celeryproject.org/>`_ to enable offline
task processing for long-running jobs like sending email notifications
and re-rendering the Knowledge Base.

Though Celery supports multiple message backends, we use `Redis <https://redis.io/>`_.


When is Celery Appropriate
==========================

You can use Celery to do any processing that doesn't need to happen in
the current request-response cycle. Examples are generating
thumbnails, sending out notification emails, updating content that
isn't about to be displayed to the user, and others.

Ask yourself the question: "Is the user going to need this data on the
page I'm about to send them?" If not, using a Celery task may be a
good choice.



Celery
======


Installing
----------

Celery (and Django-Celery) is part of our dependencies.
You shouldn't need to do any manual installation.


Configuring and Running
-----------------------

We set some reasonable defaults for Celery in ``settings.py``. These can be
overriden either in ``settings_local.py`` or via the command line when running
``celery -A kitsune worker``.

In ``settings_local.py`` you should set at least this, if you want to use
Celery::

    CELERY_TASK_ALWAYS_EAGER = False

This defaults to ``True``, which causes all task processing to be done online.
This lets you run Kitsune even if you don't have Redis or want to deal with
running workers all the time.

You can also configure the concurrency. Here is the default::

    CELERY_WORKER_CONCURRENCY = 4

Then to start the Celery workers, you just need to run::

    celery -A kitsune worker

This will start Celery with the default number of worker threads and the
default logging level. You can change those with::

    celery -A kitsune worker --loglevel=DEBUG --concurrency=10

This would start Celery with 10 worker threads and a log level of ``DEBUG``.
