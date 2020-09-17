from math import ceil
from django.core.management.base import BaseCommand

from kitsune.search.v2.es7_utils import get_doc_types, index_objects_bulk


class Command(BaseCommand):
    help = "Reindex ES7 documents"

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
            "--percentage", type=float, default=100,
        )
        parser.add_argument(
            "--bulk-count", type=int, default=100,
        )

    def handle(self, *args, **kwargs):
        doc_types = get_doc_types()

        limit = kwargs["limit"]
        if limit:
            doc_types = [dt for dt in doc_types if dt.__name__ in limit]

        progress_msg = "Indexed {progress} out of {count}"

        for dt in doc_types:
            self.stdout.write("Reindexing: {}".format(dt.__name__))

            model = dt.get_model()
            qs = model.objects.all()
            count = qs.count()

            percentage = kwargs["percentage"]
            total = count
            if percentage < 100:
                count = int(count * percentage / 100)
                qs = qs[:count]
            print("Indexing {}%, so {} documents out of {}".format(percentage, count, total))

            id_list = list(qs.values_list("pk", flat=True))
            bulk_count = kwargs["bulk_count"]

            for x in range(ceil(count / bulk_count)):
                start = x * bulk_count
                end = start + bulk_count
                index_objects_bulk.delay(dt.__name__, id_list[start:end])
                print(progress_msg.format(progress=min(end, count), count=count))
