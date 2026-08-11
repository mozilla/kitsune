"""Report the corpus volume and request load of a full retrieval ingestion.

Reads the database and runs the chunker locally. It touches no index, queues no work, and
makes no embedding call. It is read-only, but still scans and chunks the selected corpus.
"""

from django.core.management.base import BaseCommand, CommandError

from kitsune.retrieval.estimate import DEFAULT_PAGE_SIZE, estimate_ingestion


class Command(BaseCommand):
    help = "Measure the eligible corpus and predict ingestion request load without embedding."

    def add_arguments(self, parser):
        parser.add_argument(
            "--locale",
            action="append",
            default=None,
            metavar="LOCALE",
            help="Restrict to these locales; repeatable. Absent means every locale.",
        )
        parser.add_argument(
            "--page-size",
            type=int,
            default=DEFAULT_PAGE_SIZE,
            help="Database and backfill page size to use for the prediction.",
        )

    def handle(self, *args, **options):
        locales = list(dict.fromkeys(locale.strip() for locale in options["locale"] or ()))
        if any(not locale for locale in locales):
            raise CommandError("--locale must not be empty.")

        try:
            estimate = estimate_ingestion(locales=locales, page_size=options["page_size"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if not estimate.documents:
            self.stdout.write("No eligible documents; nothing would be ingested.")
            return

        write = self.stdout.write
        write(f"Eligible documents:      {estimate.documents:>10,}")
        write(f"Chunks:                  {estimate.chunks:>10,}")
        write(f"Estimated tokens:        {estimate.tokens:>10,}")
        write(f"Input characters:        {estimate.characters:>10,}")
        write("")
        write(f"Chunks per document:     mean {estimate.mean_chunks_per_document:.2f}")
        write(f"                         p50  {estimate.p50_chunks_per_document}")
        write(f"                         p95  {estimate.p95_chunks_per_document}")
        write(f"                         max  {estimate.max_chunks_per_document}")
        write("")
        write(f"Provider requests, per-document: {estimate.provider_requests_per_document:>7,}")
        write(f"Provider requests, batched:      {estimate.provider_requests_batched:>7,}")
        if estimate.request_multiplier is not None:
            write(f"Request reduction from batching: {estimate.request_multiplier:>7.1f}x")
        if estimate.documents_deferred_by_input_bound:
            write(
                f"{estimate.documents_deferred_by_input_bound:,} documents exceed the "
                "per-task input bound and would use individual-document sync."
            )

        write("")
        write(f"Largest chunk: {estimate.max_tokens_per_chunk:,} estimated tokens")
        if estimate.chunks_over_token_limit:
            # The adapter refuses a batch containing an oversized input.
            raise CommandError(
                f"{estimate.chunks_over_token_limit:,} chunks exceed the provider's per-input "
                "token limit and would fail ingestion. Fix the chunker before backfilling."
            )
