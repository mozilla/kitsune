from celery import shared_task
from django.core.management import call_command

from kitsune.sumo.decorators import skip_if_read_only_mode


@shared_task
@skip_if_read_only_mode
def update_product_details():
    call_command("update_product_details")


@shared_task
@skip_if_read_only_mode
def sync_product_versions():
    call_command("sync_product_versions")
