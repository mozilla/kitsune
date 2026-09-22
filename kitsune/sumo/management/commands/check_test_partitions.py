from collections import defaultdict
from pathlib import Path
from unittest import TestLoader

# Django also uses this discovery sentinel; unittest's type stubs omit it.
from unittest.loader import _FailedTest  # type: ignore[attr-defined]

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test.runner import filter_tests_by_tags
from django.test.utils import get_runner, iter_test_cases


class Command(BaseCommand):
    help = "Check that GitHub Actions runs every discovered Python test exactly once."
    requires_system_checks = ()
    test_labels = ("kitsune",)

    def add_arguments(self, parser):
        parser.add_argument(
            "--config",
            type=Path,
            default=Path(settings.BASE_DIR) / ".github" / "workflows" / "ci.yml",
            help="GitHub Actions workflow to check.",
        )

    def discover(self, labels):
        runner = get_runner(settings)(verbosity=0, interactive=False)
        # Isolate loader errors between discovery calls instead of sharing Django's loader.
        runner.test_loader = TestLoader()
        suite = runner.build_suite(labels)
        if runner.test_loader.errors:
            raise CommandError("Test discovery failed:\n" + "\n".join(runner.test_loader.errors))
        tests = list(iter_test_cases(suite))
        # A load_tests() hook can return failures from a different loader.
        for test in tests:
            if isinstance(test, _FailedTest):
                raise CommandError(f"Test discovery failed for {test.id()}:\n{test._exception}")
        return tests

    def handle(self, *args, **options):
        with options["config"].open() as config_file:
            config = yaml.safe_load(config_file)

        try:
            matrix = config["jobs"]["python-tests"]["strategy"]["matrix"]
        except (KeyError, TypeError) as error:
            raise CommandError("GitHub Actions python-tests matrix is missing.") from error
        if not isinstance(matrix, dict) or set(matrix) != {"include"}:
            raise CommandError("The python-tests matrix must contain only include.")
        partitions = matrix["include"]
        if not isinstance(partitions, list) or not partitions:
            raise CommandError("The python-tests matrix include must be a nonempty list.")

        expected = {test.id() for test in self.discover(self.test_labels)}
        if not expected:
            raise CommandError("No Python tests were discovered.")

        owners = defaultdict(list)
        for partition in partitions:
            if not isinstance(partition, dict):
                raise CommandError("Each python-tests matrix row must be a mapping.")
            job_name = partition.get("name")
            if not isinstance(job_name, str) or not job_name.strip():
                raise CommandError("Each python-tests matrix row must have a nonempty name.")
            app_labels = partition.get("app_labels")
            labels = app_labels.split() if isinstance(app_labels, str) else []
            if not labels:
                raise CommandError(f"{job_name}: app_labels must be a nonempty string.")
            elasticsearch = partition.get("elasticsearch")
            if not isinstance(elasticsearch, bool):
                raise CommandError(f"{job_name}: elasticsearch must be a boolean.")
            # Discover before filtering so an import error cannot be hidden by tags.
            tests = self.discover(labels)
            # The two passes in each shell runner cover all its tests, except that
            # run-unit-tests-no-es.sh excludes the es tag from both passes.
            if not elasticsearch:
                tests = filter_tests_by_tags(tests, set(), {"es"})
            for test in tests:
                owners[test.id()].append(job_name)

        errors = []
        missing = expected - owners.keys()
        if missing:
            errors.append("Tests missing from CI:\n" + "\n".join(sorted(missing)))
        duplicates = [
            f"{test_id}: {', '.join(jobs)}"
            for test_id, jobs in sorted(owners.items())
            if len(jobs) > 1
        ]
        if duplicates:
            errors.append("Tests assigned more than once:\n" + "\n".join(duplicates))
        unexpected = owners.keys() - expected
        if unexpected:
            errors.append("Tests outside the discovered suite:\n" + "\n".join(sorted(unexpected)))
        if errors:
            raise CommandError("\n\n".join(errors))

        return self.style.SUCCESS(
            f"All {len(expected)} discovered Python tests are assigned exactly once in GitHub Actions."
        )
