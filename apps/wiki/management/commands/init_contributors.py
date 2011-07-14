#TODO: Delete this code and related test once we run on production.
import time

from django.core.management.base import NoArgsCommand

from wiki.models import Document


class Command(NoArgsCommand):
    help = 'Init document.contributors for all documents.'

    def handle_noargs(self, *a, **kw):
        start = time.time()
        num = _init_contributors()
        d = time.time() - start
        print u'Updated %d documents in %0.3f seconds.' % (num, d)


def _init_contributors():
    docs = Document.objects.filter(current_revision__isnull=False)
    for doc in docs:
        contributors = []
        for rev in doc.revisions.order_by('id'):
            if (rev.is_approved or not rev.reviewed and
                not rev.creator in contributors):
                contributors.append(rev.creator)
            if doc.current_revision == rev:
                break
        doc.contributors.add(*contributors)
    return len(docs)
