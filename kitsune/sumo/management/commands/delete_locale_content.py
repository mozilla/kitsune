from collections import Counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from kitsune.announcements.models import Announcement
from kitsune.community.models import DeletedContribution
from kitsune.dashboards.models import WikiMetric
from kitsune.gallery.models import Image
from kitsune.inproduct.models import Redirect
from kitsune.kbforums.models import Post, Thread
from kitsune.questions.models import Answer, Question, QuestionLocale
from kitsune.wiki.models import Document, DraftRevision, Locale, Revision


class Command(BaseCommand):
    help = "Delete the content of locales that are no longer supported."

    def add_arguments(self, parser):
        parser.add_argument("locales", nargs="+", help="Locale codes, e.g. bm ta-LK")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without deleting anything",
        )

    def handle(self, *args, **options):
        locales = options["locales"]

        supported = [locale for locale in locales if locale in settings.SUMO_LANGUAGES]
        if supported:
            raise CommandError(f"Still supported, so not deleted: {', '.join(supported)}")

        documents = Document.objects.filter(locale__in=locales)
        questions = Question.objects.filter(locale__in=locales)
        drafts = DraftRevision.objects.filter(locale__in=locales)
        teams = Locale.objects.filter(locale__in=locales)
        images = Image.objects.filter(locale__in=locales)
        aaq_locales = QuestionLocale.objects.filter(locale__in=locales)
        metrics = WikiMetric.objects.filter(locale__in=locales)

        self.stdout.write(f"Locales: {', '.join(locales)}")
        self.stdout.write("To delete:")
        for label, count in (
            ("KB articles", documents.count()),
            ("  their edits", Revision.objects.filter(document__in=documents).count()),
            ("  their discussion threads", Thread.objects.filter(document__in=documents).count()),
            (
                "  their discussion posts",
                Post.objects.filter(thread__document__in=documents).count(),
            ),
            ("translation drafts", drafts.count()),
            ("questions", questions.count()),
            ("  their answers", Answer.objects.filter(question__in=questions).count()),
            ("locale teams", teams.count()),
            ("  their announcements", Announcement.objects.filter(locale__in=teams).count()),
            ("gallery images", images.count()),
            ("AAQ locales", aaq_locales.count()),
            ("KB metrics", metrics.count()),
        ):
            self.stdout.write(f"  {label:28} {count}")

        # Firefox in-product links depend on these, so they're only listed.
        lowered = {locale.lower() for locale in locales}
        rules = [
            rule for rule in Redirect.objects.exclude(locale="") if rule.locale.lower() in lowered
        ]
        if rules:
            self.stdout.write("In-product redirect rules for these locales (not deleted):")
            for rule in rules:
                self.stdout.write(f"  {rule.id}: {rule}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run: nothing was deleted."))
            return

        started = timezone.now()
        deleted = Counter()
        with transaction.atomic():
            # One at a time, because the contribution signals misread a queryset as the origin.
            # Articles before templates, so deleted templates don't re-render deleted articles.
            for document in documents.order_by("is_template", "id"):
                deleted.update(document.delete()[1])
            for question in questions:
                deleted.update(question.delete()[1])
            for queryset in (drafts, teams, images, aaq_locales, metrics):
                deleted.update(queryset.delete()[1])

        recorded = DeletedContribution.objects.filter(
            locale__in=locales, created__gte=started
        ).count()

        self.stdout.write(self.style.SUCCESS("Deleted:"))
        for label, count in sorted(deleted.items()):
            if count:
                self.stdout.write(f"  {label:36} {count}")
        self.stdout.write(f"Recorded {recorded} deleted contributions.")
