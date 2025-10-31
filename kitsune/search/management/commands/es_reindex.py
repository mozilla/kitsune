from dateutil.parser import parse as dateutil_parse
from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.search.es_utils import reindex
from kitsune.sumo.utils import CommandLogger


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

    def handle(self, *args, **options):
        reindex(
            limit_to_doc_types=options["limit"] or None,
            percentage_per_doc_type=options["percentage"],
            count_per_doc_type=options["count"],
            sql_chunk_size=options["sql_chunk_size"],
            elastic_chunk_size=options["elastic_chunk_size"],
            timeout=options["timeout"],
            before=options["updated_before"],
            after=options["updated_after"],
            log_query_count=options["print_sql_count"],
            logger=CommandLogger(self, options),
        )
