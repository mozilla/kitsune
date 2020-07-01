from django.core.management.base import BaseCommand
from multidb.pinning import pin_this_thread
from multidb.pinning import unpin_this_thread

from kitsune.wiki.models import Document
from kitsune.wiki.models import Revision


class Command(BaseCommand):
    help = "Fixes documents that have the current_revision set incorrectly."

    def handle(self, **options):
        try:
            # Sends all writes to the master DB. Slaves are readonly.
            pin_this_thread()

            docs = Document.objects.all()

            for d in docs:
                revs = Revision.objects.filter(document=d, is_approved=True)
                revs = list(revs.order_by("-reviewed")[:1])

                if len(revs):
                    rev = revs[0]

                    if d.current_revision != rev:
                        d.current_revision = rev
                        d.save()
                        print(d.get_absolute_url())
        finally:
            unpin_this_thread()
