"""Compare the local token estimate with the provider's own count, one locale at a time.

A batch embedding call mixes locales, so its event cannot attribute tokens to a script. This
samples each locale separately and at random, reporting the seed it used so the same sample can
be measured again. It reads the database and writes nothing, but it does make real, paid
embedding calls.
"""

import random

from django.core.management.base import BaseCommand, CommandError

from kitsune.retrieval.chunking import chunk
from kitsune.retrieval.eligibility import eligible_documents
from kitsune.retrieval.embeddings import (
    ProviderStats,
    configured_embedding_recipe,
    get_embeddings,
)
from kitsune.retrieval.sync import CONTENT_TYPE

DEFAULT_DOCUMENTS = 10
DEFAULT_MAX_CHUNKS = 200


def _count(value: int | None) -> str:
    return "unknown" if value is None else f"{value:,}"


def _ratio(estimated: int, provider: int | None) -> str:
    if provider is None or not estimated:
        return "n/a"
    return f"{provider / estimated:.2f}"


class Command(BaseCommand):
    help = (
        "Measure count_tokens against the provider's own token count, per locale. "
        "Makes real embedding calls; writes nothing."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--locale",
            action="append",
            default=None,
            metavar="LOCALE",
            help="Restrict to these locales; repeatable. Absent means every eligible locale.",
        )
        parser.add_argument(
            "--documents",
            type=int,
            default=DEFAULT_DOCUMENTS,
            help="Documents to sample per locale.",
        )
        parser.add_argument(
            "--max-chunks",
            type=int,
            default=DEFAULT_MAX_CHUNKS,
            help="Ceiling on embedded chunks per locale, bounding what the sample costs.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Reuse a reported seed to measure the same sample again.",
        )

    def handle(self, *args, **options):
        per_locale = options["documents"]
        max_chunks = options["max_chunks"]
        if per_locale < 1:
            raise CommandError("--documents must be a positive integer.")
        if max_chunks < 1:
            raise CommandError("--max-chunks must be a positive integer.")
        locales = list(dict.fromkeys(locale.strip() for locale in options["locale"] or ()))
        if any(not locale for locale in locales):
            raise CommandError("--locale must not be empty.")

        # Fails before anything is sampled or paid for if the recipe is unusable.
        recipe = configured_embedding_recipe()
        documents = eligible_documents().select_related(None).prefetch_related(None)
        if not locales:
            locales = sorted(documents.order_by().values_list("locale", flat=True).distinct())

        seed = random.randrange(2**32) if options["seed"] is None else options["seed"]
        rows = []
        for locale in locales:
            ids = list(documents.order_by().filter(locale=locale).values_list("id", flat=True))
            # Seeded per locale, so one locale's sample never depends on another's size.
            random.Random(f"{seed}:{locale}").shuffle(ids)
            chosen = ids[:per_locale]
            by_id = documents.only("html", "title").in_bulk(chosen)

            sampled = 0
            texts: list[str] = []
            for document_id in chosen:
                if not (document := by_id.get(document_id)):
                    continue
                sampled += 1
                texts.extend(
                    item.text for item in chunk(CONTENT_TYPE, document.html, title=document.title)
                )
                if len(texts) >= max_chunks:
                    break
            del texts[max_chunks:]
            if not texts:
                continue

            stats = ProviderStats()
            get_embeddings(texts, task="document", recipe=recipe, stats=stats)
            rows.append((locale, sampled, len(texts), stats))

        if not rows:
            self.stdout.write("No eligible documents in the selected locales; nothing measured.")
            return

        write = self.stdout.write
        write(f"seed: {seed}")
        write("")
        write(
            f"{'locale':<12}{'docs':>6}{'chunks':>8}"
            f"{'estimated':>12}{'provider':>12}{'actual/est':>12}"
        )
        for locale, sampled, chunks, stats in rows:
            write(
                f"{locale:<12}{sampled:>6}{chunks:>8}"
                f"{stats.estimated_token_count:>12,}"
                f"{_count(stats.provider_token_count):>12}"
                f"{_ratio(stats.estimated_token_count, stats.provider_token_count):>12}"
            )

        counts = [stats.provider_token_count for _, _, _, stats in rows]
        estimated = sum(stats.estimated_token_count for _, _, _, stats in rows)
        provider = None if any(count is None for count in counts) else sum(counts)
        write("")
        write(
            f"{'total':<12}{sum(row[1] for row in rows):>6}{sum(row[2] for row in rows):>8}"
            f"{estimated:>12,}{_count(provider):>12}{_ratio(estimated, provider):>12}"
        )
