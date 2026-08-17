import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from kitsune.retrieval.embeddings import EmbeddingRecipe, EmbeddingUnavailable

RECIPE = EmbeddingRecipe("fake", "model", 2, "document", "query", "none")


class EvaluateRetrievalCommandTests(SimpleTestCase):
    def test_evaluate_writes_once_and_warns_about_result_identities(self):
        output = StringIO()
        with TemporaryDirectory() as directory:
            path = f"{directory}/report.json"
            with (
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval."
                    "resolve_read_target_and_recipe",
                    return_value=("retrieval-1", RECIPE),
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval."
                    "Command._read_artifact",
                    return_value=mock.sentinel.artifact,
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval.read_index_meta",
                    return_value={"mapping": {"similarity": "cosine"}},
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval."
                    "similarity_profile_fingerprint",
                    return_value=("similarity-profile", "a" * 64),
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval."
                    "is_valid_similarity_floor",
                    return_value=True,
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval.evaluate_artifacts",
                    return_value={"aggregate": "result"},
                ) as evaluate,
            ):
                call_command(
                    "evaluate_retrieval",
                    "evaluate",
                    "--environment",
                    "stage",
                    "--positive",
                    "positive.json",
                    "--no-answer",
                    "no-answer.json",
                    "--split",
                    "tuning",
                    "--similarity-floor",
                    "0.75",
                    "--output",
                    path,
                    stdout=output,
                )
                with self.assertRaisesMessage(CommandError, "Refusing to overwrite"):
                    call_command(
                        "evaluate_retrieval",
                        "evaluate",
                        "--environment",
                        "stage",
                        "--positive",
                        "positive.json",
                        "--no-answer",
                        "no-answer.json",
                        "--split",
                        "tuning",
                        "--similarity-floor",
                        "0.75",
                        "--output",
                        path,
                    )

            self.assertEqual(json.loads(Path(path).read_text()), {"aggregate": "result"})

        evaluate.assert_called_once()
        self.assertIn("result identities", output.getvalue())

    def test_freeze_rejects_an_artifact_without_both_splits(self):
        with TemporaryDirectory() as directory:
            input_path = f"{directory}/input.json"
            output_path = f"{directory}/artifact.json"
            Path(input_path).write_text(json.dumps([{"query": "one query", "locale": "en-US"}]))

            with (
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval."
                    "resolve_read_target_and_recipe",
                    return_value=("retrieval-1", RECIPE),
                ),
                self.assertRaisesMessage(CommandError, "tuning and one holdout"),
            ):
                call_command(
                    "evaluate_retrieval",
                    "freeze-no-answer",
                    "--environment",
                    "stage",
                    "--input",
                    input_path,
                    "--output",
                    output_path,
                )

    def test_provider_failure_is_readable_and_writes_no_report(self):
        with TemporaryDirectory() as directory:
            path = f"{directory}/report.json"
            with (
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval."
                    "resolve_read_target_and_recipe",
                    return_value=("retrieval-1", RECIPE),
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval."
                    "Command._read_artifact",
                    return_value=mock.sentinel.artifact,
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval.read_index_meta",
                    return_value={"mapping": {"similarity": "cosine"}},
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval."
                    "similarity_profile_fingerprint",
                    return_value=("similarity-profile", "a" * 64),
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval."
                    "is_valid_similarity_floor",
                    return_value=True,
                ),
                mock.patch(
                    "kitsune.retrieval.management.commands.evaluate_retrieval.evaluate_artifacts",
                    side_effect=EmbeddingUnavailable("provider detail"),
                ),
                self.assertRaisesMessage(CommandError, "EmbeddingUnavailable"),
            ):
                call_command(
                    "evaluate_retrieval",
                    "evaluate",
                    "--environment",
                    "stage",
                    "--positive",
                    "positive.json",
                    "--no-answer",
                    "no-answer.json",
                    "--split",
                    "tuning",
                    "--similarity-floor",
                    "0.75",
                    "--output",
                    path,
                )
            self.assertFalse(Path(path).exists())
