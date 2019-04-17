from django.core.management.base import BaseCommand

from kitsune.search.tasks import index_task
from kitsune.wiki.models import DocumentMappingType


class Command(BaseCommand):
    help = "Reindex wiki_document."

    def handle(self, **options):
        index_task.delay(DocumentMappingType, DocumentMappingType.get_indexable())
