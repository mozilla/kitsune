import sys
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest.mock import patch

import yaml
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from kitsune.sumo.management.commands.check_test_partitions import Command


class TestPartitionTests(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.package = self.root / "partition_fixtures"
        self.package.mkdir()
        (self.package / "__init__.py").touch()
        (self.package / "test_cases.py").write_text(
            dedent("""\
                from unittest import TestCase

                from django.test import tag


                class RegularTests(TestCase):
                    def test_parallel(self):
                        self.fail("Discovery must not execute tests")

                    @tag("no_parallel")
                    def test_serial(self):
                        self.fail("Discovery must not execute tests")


                @tag("es")
                class SearchTests(TestCase):
                    def test_search(self):
                        self.fail("Discovery must not execute tests")

                    @tag("no_parallel")
                    def test_serial_search(self):
                        self.fail("Discovery must not execute tests")
                """)
        )
        self.enterContext(patch.object(sys, "path", [str(self.root), *sys.path]))
        self.enterContext(patch.object(Command, "test_labels", ("partition_fixtures",)))
        self.addCleanup(self.unload_fixtures)
        self.config = {
            "jobs": {
                "general-tests": {
                    "steps": [{"run-tests-no-es": {"app_labels": "partition_fixtures"}}]
                },
                "search-tests": {
                    "steps": [
                        {
                            "run-tests-with-es": {
                                "app_labels": "partition_fixtures.test_cases.SearchTests"
                            }
                        }
                    ]
                },
            },
            "workflows": {
                "version": 2,
                "tests": {"jobs": ["general-tests", {"search-tests": {"name": "search"}}]},
            },
        }

    def unload_fixtures(self):
        for name in list(sys.modules):
            if name == "partition_fixtures" or name.startswith("partition_fixtures."):
                del sys.modules[name]

    def check_partitions(self):
        config_path = self.root / "config.yml"
        config_path.write_text(yaml.safe_dump(self.config))
        return call_command(
            "check_test_partitions", config=config_path, stdout=StringIO(), stderr=StringIO()
        )

    def test_valid_partitions_cover_regular_serial_and_es_tests(self):
        self.assertRegex(self.check_partitions(), r"\b4\b")

    def test_partial_app_assignment_leaves_a_test_uncovered(self):
        self.config["jobs"]["general-tests"]["steps"][0]["run-tests-no-es"]["app_labels"] = (
            "partition_fixtures.test_cases.RegularTests.test_parallel"
        )
        with self.assertRaises(CommandError) as error:
            self.check_partitions()
        self.assertIn(
            "partition_fixtures.test_cases.RegularTests.test_serial", str(error.exception)
        )

    def test_overlapping_partitions_report_test_and_both_jobs(self):
        self.config["jobs"]["search-tests"]["steps"][0]["run-tests-with-es"]["app_labels"] = (
            "partition_fixtures"
        )
        with self.assertRaises(CommandError) as error:
            self.check_partitions()
        message = str(error.exception)
        self.assertIn("partition_fixtures.test_cases.RegularTests.test_parallel", message)
        self.assertIn("general-tests", message)
        self.assertIn("search-tests", message)

    def test_no_es_job_excludes_es_tests_even_when_also_tagged_serial(self):
        self.config["jobs"]["search-tests"]["steps"] = [
            {"run-tests-no-es": {"app_labels": "partition_fixtures.test_cases.SearchTests"}}
        ]
        with self.assertRaises(CommandError) as error:
            self.check_partitions()
        message = str(error.exception)
        self.assertIn("partition_fixtures.test_cases.SearchTests.test_search", message)
        self.assertIn("partition_fixtures.test_cases.SearchTests.test_serial_search", message)

    def test_job_definition_without_workflow_invocation_does_not_cover_tests(self):
        self.config["workflows"]["tests"]["jobs"] = ["general-tests"]
        with self.assertRaises(CommandError) as error:
            self.check_partitions()
        self.assertIn(
            "partition_fixtures.test_cases.SearchTests.test_search", str(error.exception)
        )

    def test_empty_labels_do_not_fall_back_to_full_discovery(self):
        self.config["jobs"]["general-tests"]["steps"][0]["run-tests-no-es"]["app_labels"] = ""
        with self.assertRaises(CommandError) as error:
            self.check_partitions()
        self.assertIn("general-tests", str(error.exception))

    def test_import_error_cannot_count_as_a_covered_test(self):
        (self.package / "test_broken.py").write_text(
            'raise ImportError("partition fixture dependency is missing")\n'
        )
        with self.assertRaises(CommandError) as error:
            self.check_partitions()
        self.assertIn("ImportError: partition fixture dependency is missing", str(error.exception))

    def test_invalid_partition_label_reports_discovery_error(self):
        self.config["jobs"]["general-tests"]["steps"][0]["run-tests-no-es"]["app_labels"] = (
            "partition_fixtures.missing"
        )
        with self.assertRaises(CommandError) as error:
            self.check_partitions()
        self.assertIn("partition_fixtures.missing", str(error.exception))

    def test_failure_returned_by_another_loader_cannot_count_as_covered(self):
        (self.package / "test_nested.py").write_text(
            dedent("""\
                from unittest import TestLoader

                def load_tests(loader, tests, pattern):
                    return TestLoader().loadTestsFromName("missing_nested_loader_dependency")
                """)
        )
        with self.assertRaises(CommandError) as error:
            self.check_partitions()
        self.assertIn("missing_nested_loader_dependency", str(error.exception))
