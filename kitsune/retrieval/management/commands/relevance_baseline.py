"""Derive a golden set from solved questions and score today's keyword search against it.

Read-only: it queries the database and the existing lexical index, and writes nothing except
the fixture file it is asked for. Full scoring sends one search request per pair and should be
run with the same care as any other corpus-wide production operation.

The resulting number is a floor, not a verdict. The set is enriched for questions filed after
search did not help, so absolute recall is likely pessimistic. What makes it useful is that a
later retrieval system can be scored on the identical pairs.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from kitsune.retrieval.evaluation import (
    DEFAULT_K_VALUES,
    DERIVATION,
    GoldenSet,
    build_golden_set,
    score_lexical_search,
)


class Command(BaseCommand):
    help = "Score today's keyword search against a golden set derived from solved questions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--locale",
            action="append",
            default=None,
            metavar="LOCALE",
            help="Restrict to these locales; repeatable. Absent means every locale.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Stop after this many pairs. Scoring runs one search per pair.",
        )
        parser.add_argument(
            "--write",
            metavar="PATH",
            default=None,
            help="Write the set, including user-written query text, to this JSON file.",
        )
        parser.add_argument(
            "--read",
            metavar="PATH",
            default=None,
            help="Score a previously written set instead of deriving a new one.",
        )
        parser.add_argument(
            "--derive-only",
            action="store_true",
            help="Build the set without scoring it (no searches are run).",
        )

    def handle(self, *args, **options):
        if options["read"] and (options["locale"] or options["limit"]):
            raise CommandError("--read scores a fixed set; --locale and --limit do not apply.")
        if options["limit"] is not None and options["limit"] <= 0:
            raise CommandError("--limit must be a positive integer.")

        locales = list(dict.fromkeys(locale.strip() for locale in options["locale"] or ()))
        if any(not locale for locale in locales):
            raise CommandError("--locale must not be empty.")
        golden = (
            self._load(Path(options["read"]))
            if options["read"]
            else build_golden_set(locales=locales, limit=options["limit"])
        )

        if options["write"]:
            try:
                Path(options["write"]).write_text(golden.to_json(), encoding="utf-8")
            except OSError as exc:
                raise CommandError(f"Could not write {options['write']}: {exc}") from exc
            self.stdout.write(f"Wrote {len(golden.pairs)} pairs to {options['write']}.")
            self.stdout.write(
                self.style.WARNING(
                    "This fixture contains user-generated question text and IDs; "
                    "handle and distribute it accordingly."
                )
            )

        self.stdout.write(f"Golden set:   {len(golden.pairs):,} pairs")
        self.stdout.write(f"Generation:   {golden.generation}")
        self.stdout.write(f"Derivation:   {golden.derivation}")
        if not golden.pairs:
            self.stdout.write("No labelled pairs; nothing to score.")
            return
        if options["derive_only"]:
            return

        self.stdout.write("")
        self.stdout.write(f"Scoring {len(golden.pairs):,} queries against today's search...")
        score = score_lexical_search(golden)

        self.stdout.write("")
        for k in DEFAULT_K_VALUES:
            self.stdout.write(f"  recall@{k:<3} {score.recall_at_k[k]:.3f}")
        self.stdout.write(f"  nDCG@10   {score.ndcg_at_10:.3f}")
        if score.empty_results:
            self.stdout.write(
                f"  {score.empty_results:,} queries returned no results at all "
                "(a different failure from returning the wrong thing)."
            )
        self.stdout.write("")
        self.stdout.write(
            "These pairs are enriched for cases where search did not help, so treat this as a "
            "floor. Compare a later system on the same pairs rather than reading it absolutely."
        )

    def _load(self, path):
        if not path.is_file():
            raise CommandError(f"{path} does not exist.")
        try:
            golden = GoldenSet.from_json(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CommandError(f"{path} is not a golden set: {exc}") from exc
        if golden.derivation != DERIVATION:
            # Comparing across derivation rules silently compares different questions.
            raise CommandError(
                f"{path} was derived by {golden.derivation!r}, but this code derives "
                f"{DERIVATION!r}. Re-derive the set before comparing scores."
            )
        return golden
