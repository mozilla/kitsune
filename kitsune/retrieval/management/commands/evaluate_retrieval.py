"""Freeze current-environment evaluation artifacts and run one explicit comparison."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from elasticsearch import ApiError, TransportError

from kitsune.retrieval.embeddings import EmbeddingUnavailable
from kitsune.retrieval.evaluation import (
    EvaluationArtifact,
    EvaluationConfig,
    InvalidEvaluationArtifact,
    build_positive_artifact,
    evaluate_artifacts,
    freeze_no_answer_artifact,
    validate_split_coverage,
)
from kitsune.retrieval.fingerprints import (
    is_valid_similarity_floor,
    read_index_meta,
    similarity_profile_fingerprint,
)
from kitsune.retrieval.index import RetrievalIndexUnavailable, resolve_read_target_and_recipe


class Command(BaseCommand):
    help = "Freeze or evaluate current-environment retrieval relevance artifacts."

    def add_arguments(self, parser):
        actions = parser.add_subparsers(dest="action", required=True)

        derive = actions.add_parser(
            "derive-positive",
            help="Derive a frozen positive artifact from solved-question KB citations.",
        )
        self._add_artifact_arguments(derive)
        derive.add_argument(
            "--locale",
            action="append",
            default=None,
            help="Restrict derivation to this locale; repeatable.",
        )
        derive.add_argument("--limit", type=int, default=None)

        freeze = actions.add_parser(
            "freeze-no-answer",
            help="Freeze a manually reviewed JSON list of no-answer queries.",
        )
        self._add_artifact_arguments(freeze)
        freeze.add_argument("--input", required=True, metavar="PATH")

        evaluate = actions.add_parser(
            "evaluate",
            help="Evaluate one configuration against frozen artifacts.",
        )
        self._add_artifact_arguments(evaluate)
        evaluate.add_argument("--positive", required=True, metavar="PATH")
        evaluate.add_argument("--no-answer", required=True, metavar="PATH")
        evaluate.add_argument("--split", required=True, choices=("tuning", "holdout"))
        evaluate.add_argument("--similarity-floor", required=True, type=float)
        evaluate.add_argument("--semantic-k", type=int, default=settings.RETRIEVAL_SEMANTIC_K)
        evaluate.add_argument(
            "--num-candidates",
            type=int,
            default=settings.RETRIEVAL_KNN_NUM_CANDIDATES,
        )
        evaluate.add_argument(
            "--rank-window-size",
            type=int,
            default=settings.RETRIEVAL_RRF_RANK_WINDOW_SIZE,
        )
        evaluate.add_argument(
            "--default-operator",
            choices=("AND", "OR"),
            default=settings.RETRIEVAL_LEXICAL_DEFAULT_OPERATOR,
        )
        evaluate.add_argument("--minimum-should-match", default=None)
        evaluate.add_argument(
            "--locale-composition",
            choices=("combined", "separate"),
            default=settings.RETRIEVAL_LOCALE_COMPOSITION,
        )

    @staticmethod
    def _add_artifact_arguments(parser):
        parser.add_argument(
            "--environment",
            required=True,
            help="Explicit environment identity stored in and checked against the artifact.",
        )
        parser.add_argument("--output", required=True, metavar="PATH")

    def handle(self, *args, **options):
        if options.get("limit") is not None and options["limit"] <= 0:
            raise CommandError("--limit must be a positive integer")
        output_path = Path(options["output"])
        if output_path.exists():
            raise CommandError(f"Refusing to overwrite existing file {output_path}")

        try:
            read_generation, recipe = resolve_read_target_and_recipe()
            match options["action"]:
                case "derive-positive":
                    locales = tuple(
                        dict.fromkeys(locale.strip() for locale in options["locale"] or ())
                    )
                    if any(not locale for locale in locales):
                        raise CommandError("--locale must not be empty")
                    artifact = build_positive_artifact(
                        environment=options["environment"],
                        read_generation=read_generation,
                        locales=locales,
                        limit=options["limit"],
                    )
                    validate_split_coverage(artifact)
                    payload = artifact.to_json()
                    summary = f"Frozen {len(artifact.queries):,} positive queries"
                case "freeze-no-answer":
                    raw = self._read_json(Path(options["input"]))
                    records = raw.get("queries") if isinstance(raw, dict) else raw
                    if not isinstance(records, list):
                        raise CommandError("no-answer input must be a JSON list of query records")
                    artifact = freeze_no_answer_artifact(
                        records,
                        environment=options["environment"],
                        read_generation=read_generation,
                    )
                    validate_split_coverage(artifact)
                    payload = artifact.to_json()
                    summary = f"Frozen {len(artifact.queries):,} no-answer queries"
                case "evaluate":
                    positive = self._read_artifact(Path(options["positive"]))
                    no_answer = self._read_artifact(Path(options["no_answer"]))
                    meta = read_index_meta(read_generation)
                    _, similarity_profile = similarity_profile_fingerprint(meta)
                    if not is_valid_similarity_floor(
                        options["similarity_floor"], meta["mapping"]["similarity"]
                    ):
                        raise CommandError(
                            "--similarity-floor is invalid for the read generation's metric"
                        )
                    minimum_should_match = options["minimum_should_match"]
                    if options["default_operator"] == "OR" and not minimum_should_match:
                        minimum_should_match = settings.RETRIEVAL_LEXICAL_MINIMUM_SHOULD_MATCH
                    config = EvaluationConfig(
                        similarity_floor=options["similarity_floor"],
                        similarity_profile=similarity_profile,
                        semantic_k=options["semantic_k"],
                        num_candidates=options["num_candidates"],
                        rank_window_size=options["rank_window_size"],
                        default_operator=options["default_operator"],
                        minimum_should_match=minimum_should_match,
                        locale_composition=options["locale_composition"],
                    )
                    report = evaluate_artifacts(
                        positive,
                        no_answer,
                        environment=options["environment"],
                        read_generation=read_generation,
                        recipe=recipe,
                        config=config,
                        split=options["split"],
                    )
                    payload = json.dumps(report, indent=2, ensure_ascii=False)
                    summary = f"Evaluated the {options['split']} split"
                case _:
                    raise CommandError("unknown evaluation action")
        except (InvalidEvaluationArtifact, RetrievalIndexUnavailable, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        except (ApiError, EmbeddingUnavailable, TransportError) as exc:
            raise CommandError(f"evaluation failed: {type(exc).__name__}") from exc

        self._write(output_path, payload)
        self.stdout.write(f"{summary} against {read_generation}.")
        self.stdout.write(f"Wrote {options['output']}.")
        self.stdout.write(
            self.style.WARNING(
                "This file contains public user-authored queries or result identities; keep it "
                "in a controlled temporary location and delete it after recording the artifact "
                "digests, selected configuration, aggregate results, and decision."
            )
        )

    @staticmethod
    def _read_json(path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Could not read {path}: {exc}") from exc

    def _read_artifact(self, path: Path) -> EvaluationArtifact:
        return EvaluationArtifact.from_json(self._read_json(path))

    @staticmethod
    def _write(path: Path, payload: str) -> None:
        try:
            with path.open("x", encoding="utf-8") as output:
                output.write(f"{payload}\n")
        except FileExistsError as exc:
            raise CommandError(f"Refusing to overwrite existing file {path}") from exc
        except OSError as exc:
            raise CommandError(f"Could not write {path}: {exc}") from exc
