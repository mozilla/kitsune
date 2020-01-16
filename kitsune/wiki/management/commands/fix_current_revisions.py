from django.core.management.base import BaseCommand
from django_statsd.clients import statsd
from multidb.pinning import pin_this_thread, unpin_this_thread

from kitsune.wiki.models import Document, Revision


class Command(BaseCommand):
    help = "Fixes documents that have the current_revision set incorrectly."

    def handle(self, **options):
        try:
            # Sends all writes to the master DB. Slaves are readonly.
            pin_this_thread()

            docs = Document.objects.all()

            for d in docs:
                revs = Revision.objects.filter(document=d, is_approved=True)
                revs = list(revs.order_by('-reviewed')[:1])

                if len(revs):
                    rev = revs[0]

                    if d.current_revision != rev:
                        d.current_revision = rev
                        d.save()
                        print(d.get_absolute_url())
                        statsd.incr('wiki.cron.fix-current-revision')
        finally:
            unpin_this_thread()
