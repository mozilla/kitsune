"""Compare the labels in translated articles with the official labels."""

import csv
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from kitsune.llm.l10n.ui_labels.report import Finding, check_article, get_english_articles

# Each worker keeps a database connection while it checks an article.
POOL_SIZE = settings.DATABASES["default"]["OPTIONS"]["pool"]["max_size"]


class Command(BaseCommand):
    help = "Work with the official translations of the UI labels in Knowledge Base articles."

    def add_arguments(self, parser):
        actions = parser.add_subparsers(dest="action", required=True)
        about_report = (
            "Compare the labels in translations with the official labels. No articles are changed."
        )
        report = actions.add_parser("report", help=about_report, description=about_report)
        report.add_argument("--locale", help="Only these locales, like fr,de.")
        report.add_argument("--limit", type=int, help="Only this many English articles.")
        report.add_argument(
            "--workers",
            type=int,
            default=POOL_SIZE,
            choices=range(1, POOL_SIZE + 1),
            help="How many articles to check at a time. Each needs a database connection, "
            "so the most is the size of the database pool (DB_POOL_MAX_SIZE).",
        )
        report.add_argument("--output", help="Write everything the check found to this CSV file.")

    def handle(self, *args, **options):
        getattr(self, options["action"])(**options)

    def report(self, locale, limit, workers, output, **options):
        locales = locale.split(",") if locale else None

        def check(article):
            try:
                return check_article(article, locales)
            except Exception as error:
                # One article that fails must not stop the run. Its answers so far are saved.
                self.stderr.write(f"{article.slug}: {type(error).__name__}: {error}")
                return None
            finally:
                if workers > 1:
                    connection.close()

        articles = list(get_english_articles()[:limit])
        if workers > 1:
            connection.close()
            with ThreadPoolExecutor(workers) as pool:
                found = list(pool.map(check, articles))
        else:
            found = [check(article) for article in articles]
        findings = [finding for of_article in found if of_article for finding in of_article]

        by_locale: dict[str, Counter] = defaultdict(Counter)
        for finding in findings:
            by_locale[finding.locale][finding.result] += 1
        for found_locale, counts in sorted(by_locale.items()):
            self.stdout.write(f"\n{found_locale}")
            for result, count in counts.most_common():
                self.stdout.write(f"  {count:>6}  {result}")
        if failed := found.count(None):
            self.stdout.write(f"\n{failed} of {len(articles)} articles failed and aren't counted.")
        if output:
            with open(output, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(Finding._fields)
                writer.writerows(findings)
