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
            "--percentage", type=float, default=100, help="Index a percentage of total documents",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=None,
            help="Index a set number of documents per type (overrides --percentage)",
        )
        parser.add_argument(
            "--bulk-count", type=int, default=100, help="Index this number of documents at once",
        )
        parser.add_argument(
            "--print-sql-count",
            action="store_true",
            help="Print the number of SQL statements executed",
        )

    def handle(self, *args, **kwargs):
        doc_types = get_doc_types()

        limit = kwargs["limit"]
        if limit:
            doc_types = [dt for dt in doc_types if dt.__name__ in limit]

        progress_msg = "Indexed {progress} out of {count}"

        if kwargs["print_sql_count"]:
            from django.db import connection, reset_queries

        for dt in doc_types:
            self.stdout.write("Reindexing: {}".format(dt.__name__))

            model = dt.get_model()
            qs = model.objects.all()
            total = qs.count()
            count = kwargs["count"]

            percentage = kwargs["percentage"]
            if count:
                print("Indexing {} documents out of {}".format(count, total))
            else:
                if percentage < 100:
                    count = int(total * percentage / 100)
                    qs = qs[:count]
                else:
                    count = total
                print("Indexing {}%, so {} documents out of {}".format(percentage, count, total))

            id_list = list(qs.values_list("pk", flat=True))
            bulk_count = kwargs["bulk_count"]

            for x in range(ceil(count / bulk_count)):
                start = x * bulk_count
                end = start + bulk_count
                index_objects_bulk.delay(dt.__name__, id_list[start:end])
                if kwargs["print_sql_count"]:
                    print("{} SQL queries executed".format(len(connection.queries)))
                    reset_queries()
                print(progress_msg.format(progress=min(end, count), count=count))
