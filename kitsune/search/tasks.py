import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from kitsune.search.es_utils import reindex

log = logging.getLogger("k.task")


@shared_task
def reindex_recent():
    # Index items that have changed within the last 90 minutes.
    reindex(after=timezone.now() - timedelta(minutes=90), logger=log)
