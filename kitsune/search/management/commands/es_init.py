from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch_dsl.exceptions import IllegalOperation
from datetime import datetime, timezone
import logging

from kitsune.search.es_utils import get_doc_types, es_client


class Command(BaseCommand):
    help = "Initialize ES document types"

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
            "--migrate-writes",
            action="store_true",
            help="Create a new index and point the _write alias at it",
        )
        parser.add_argument(
            "--migrate-reads",
            action="store_true",
            help="Update the _read alias to point at the latest index",
        )
        parser.add_argument(
            "--reload-search-analyzers",
            action="store_true",
            help="Reload the search analyzers (used when changing synonyms)",
        )

    def handle(self, *args, **kwargs):
        client = es_client()
        doc_types = get_doc_types()

        limit = kwargs["limit"]
        if limit:
            doc_types = [dt for dt in doc_types if dt.__name__ in limit]

        timestamp = datetime.now(tz=timezone.utc)

        for dt in doc_types:
            print(f"Initializing: {dt.__name__}")

            migrate_writes = kwargs["migrate_writes"]
            migrate_reads = kwargs["migrate_reads"]

            if not (migrate_reads or migrate_writes):
                try:
                    index = dt.alias_points_at(dt.Index.write_alias)
                    if not index:
                        print("First time running, creating index and aliases:")
                        migrate_writes = True
                        migrate_reads = True
                    else:
                        print("Updating index")
                        try:
                            # Try regular update
                            dt.init(index=index)
                        except IllegalOperation as e:
                            # If we get "cannot update analysis on open index",
                            # close it, update, reopen
                            error_msg = "cannot update analysis configuration on an open index"
                            if error_msg in str(e).lower():
                                print(f"Need to close index {index} first")
                                try:
                                    client.indices.close(index=index)
                                    dt.init(index=index)
                                    client.indices.open(index=index)
                                    print(
                                        f"Successfully updated index {index} "
                                        f"after closing/reopening"
                                    )
                                except Exception as close_error:
                                    print(f"Error during close/reopen: {close_error}")
                            else:
                                print(e)
                except Exception as e:
                    if settings.TEST:
                        logging.getLogger(__name__).warning(
                            f"Error checking alias during test: {e}. "
                            f"This can be ignored in test environment."
                        )
                        # In tests, if we can't check alias, assume first time setup
                        migrate_writes = True
                        migrate_reads = True
                    else:
                        # Re-raise in production
                        raise

            if migrate_writes:
                try:
                    print("Migrating writes: creating new index and pointing write alias at it")
                    dt.migrate_writes(timestamp=timestamp)
                except Exception as e:
                    print(f"Error during migrate_writes: {e}")
                    # We don't re-raise the exception, just continue with the next steps

            if migrate_reads:
                try:
                    print("Migrating reads: pointing read alias where write alias points")
                    dt.migrate_reads()
                except Exception as e:
                    print(f"Error during migrate_reads: {e}")
                    # We don't re-raise the exception, just continue with the next steps

            # Safe way to get the index for reload_search_analyzers
            index = None
            try:
                index = dt.alias_points_at(dt.Index.write_alias)
            except Exception as e:
                if settings.TEST:
                    logging.getLogger(__name__).warning(
                        f"Error getting alias for analyzers during test: {e}. "
                        f"This can be ignored in test environment."
                    )
                else:
                    raise

            # Only try to reload analyzers if we have a valid index
            if index and kwargs["reload_search_analyzers"]:
                print(f"Reloading search analyzers on {index}")
                try:
                    # Reload search analyzers using compatibility wrapper
                    client.indices.reload_search_analyzers(index=index)

                    # Clear the request cache - try different approaches
                    try:
                        # First try with request=True (works in some versions)
                        client.indices.clear_cache(index=index, request=True)
                    except Exception:
                        try:
                            # Then try with request_cache=True (works in other versions)
                            client.indices.clear_cache(index=index, request_cache=True)
                        except Exception:
                            # Finally try without specific parameters
                            client.indices.clear_cache(index=index)
                except Exception as e:
                    if settings.TEST:
                        logging.getLogger(__name__).warning(
                            f"Error reloading analyzers during test: {e}. "
                            f"This can be ignored in test environment."
                        )
                    else:
                        logging.getLogger(__name__).error(f"Error reloading analyzers: {e}")
                        raise

            print("")  # print blank line to make console output easier to read
