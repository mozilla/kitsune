from math import ceil

from dateutil.parser import parse as dateutil_parse
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries

from kitsune.search.es_utils import get_doc_types, index_objects_bulk


class Command(BaseCommand):
    help = "Reindex ES documents"

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
            "--percentage",
            type=float,
            default=100,
            help="Index a percentage of total documents",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=None,
            help="Index a set number of documents per type (overrides --percentage)",
        )
        parser.add_argument(
            "--sql-chunk-size",
            type=int,
            default=settings.ES_DEFAULT_SQL_CHUNK_SIZE,
            help="Retrieve this number of documents from SQL in each Celery job",
        )
        parser.add_argument(
            "--elastic-chunk-size",
            type=int,
            default=settings.ES_DEFAULT_ELASTIC_CHUNK_SIZE,
            help="Send this number of documents to ElasticSearch in each bulk request",
        )
        parser.add_argument(
            "--timeout",
            type=float,
            default=settings.ES_BULK_DEFAULT_TIMEOUT,
            help="Set the request timeout (in seconds)",
        )
        parser.add_argument(
            "--updated-before",
            type=dateutil_parse,
            default=None,
            help="Only index model instances updated before this date",
        )
        parser.add_argument(
            "--updated-after",
            type=dateutil_parse,
            default=None,
            help="Only index model instances updated after this date",
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

        for dt in doc_types:
            self.stdout.write(f"Reindexing: {dt.__name__}")

            model = dt.get_model()

            before = kwargs["updated_before"]
            after = kwargs["updated_after"]
            if before or after:
                try:
                    qs = model.objects_range(before=before, after=after)
                except NotImplementedError:
                    print(
                        f"{model} hasn't implemeneted an `updated_column_name` property."
                        "No documents will be indexed of this type."
                    )
                    continue
            else:
                qs = model._default_manager.all()

            total = qs.count()
            count = kwargs["count"]

            percentage = kwargs["percentage"]
            if count:
                print(f"Indexing {count} documents out of {total}")
            else:
                if percentage < 100:
                    count = int(total * percentage / 100)
                    qs = qs[:count]
                else:
                    count = total
                print(f"Indexing {percentage}%, so {count} documents out of {total}")

            id_list = list(qs.values_list("pk", flat=True))
            sql_chunk_size = kwargs["sql_chunk_size"]

            # slice the list of ids into chunks of `sql_chunk_size` and send a task to celery
            # to process each chunk. we do this so as to not OOM on celery when processing
            # tens of thousands of documents
            for x in range(ceil(count / sql_chunk_size)):
                start = x * sql_chunk_size
                end = start + sql_chunk_size
                # Make sure all parameters are passed as keyword arguments
                index_objects_bulk.delay(
                    dt.__name__,
                    id_list[start:end],
                    timeout=kwargs["timeout"],
                    elastic_chunk_size=kwargs["elastic_chunk_size"],
                )
                if kwargs["print_sql_count"]:
                    print(f"{len(connection.queries)} SQL queries executed")
                    reset_queries()
                print(progress_msg.format(progress=min(end, count), count=count))
