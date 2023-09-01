from django.core.management.base import BaseCommand
from django.db.models import F

from kitsune.wiki.models import Document, Revision


class Command(BaseCommand):
    help = "Fixes documents that have the current_revision set incorrectly."

    def handle(self, **options):
        # Reduce memory usage by only loading the columns we need.
        docs = Document.objects.all().values("id", "current_revision_id")

        for d in docs.iterator():
            revs = Revision.objects.filter(document_id=d["id"], is_approved=True)
            revs = revs.order_by(F("reviewed").desc(nulls_last=True)).values_list("id", flat=True)[
                :1
            ]

            if len(revs):
                rev_id = revs[0]

                if d["current_revision_id"] != rev_id:
                    doc = Document.objects.get(id=d["id"])
                    doc.current_revision_id = rev_id
                    doc.save()
                    print(doc.get_absolute_url())
