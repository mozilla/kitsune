from django.core.management.base import BaseCommand
from elasticsearch7.exceptions import NotFoundError

from kitsune.search.v2.es7_utils import get_doc_types


class Command(BaseCommand):
    help = "Initialize ES7 document types"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=str,
            dest="limit",
            nargs="*",
            default="",
            help="Limit to specific doc types",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete indices before creating",
        )

    def handle(self, *args, **kwargs):
        doc_types = get_doc_types()

        limit = kwargs["limit"]
        if limit:
            doc_types = [dt for dt in doc_types if dt.__name__ in limit]

        for dt in doc_types:
            self.stdout.write("Initializing: {}".format(dt.__name__))
            if kwargs["delete"]:
                try:
                    dt._index.delete()
                except NotFoundError:
                    pass
            dt.init()
