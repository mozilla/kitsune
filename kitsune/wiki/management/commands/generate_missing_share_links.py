from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.wiki import tasks
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.models import Document


class Command(BaseCommand):
    help = "Generate share links for documents that may be missing them."

    def handle(self, **options):
        document_ids = (
            Document.objects.select_related("revision")
            .filter(
                parent=None,
                share_link="",
                is_template=False,
                is_archived=False,
                category__in=settings.IA_DEFAULT_CATEGORIES,
            )
            .exclude(slug="", current_revision=None, html__startswith=REDIRECT_HTML)
            .values_list("id", flat=True)
        )

        tasks.add_short_links.delay(list(document_ids))
