.. _celery-chapter:

======
Celery
======

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


Configuring and Running
=======================

Celery will automatically start when you run::

    make run

We set some reasonable defaults for Celery in ``settings.py``.
These can be overriden in ``.env``.

If you don't want to use Celery, you can set this in ``.env``::

    CELERY_TASK_ALWAYS_EAGER = True

Setting this to ``True`` causes all task processing to be done online.
This is useful when debugging tasks, for instance.

You can also configure the concurrency. Here is the default::

    CELERY_WORKER_CONCURRENCY = 4

Then to restart the Celery workers, you just need to run::

    docker-compose restart celery
