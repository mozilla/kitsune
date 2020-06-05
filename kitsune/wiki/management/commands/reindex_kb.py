from django.core.management.base import BaseCommand

from kitsune.search.tasks import index_task
from kitsune.search.utils import to_class_path
from kitsune.wiki.models import DocumentMappingType


class Command(BaseCommand):
    help = "Reindex wiki_document."

    def handle(self, **options):
        index_task.delay(to_class_path(DocumentMappingType),
                         DocumentMappingType.get_indexable())
