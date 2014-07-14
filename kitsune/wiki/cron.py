import cronjobs
import waffle

from itertools import chain

from django.conf import settings
from django.db.models import F, Q, ObjectDoesNotExist

from statsd import statsd
from tower import ugettext as _

from kitsune.products.models import Product
from kitsune.search.tasks import index_task
from kitsune.sumo import email_utils
from kitsune.wiki import tasks
from kitsune.wiki.models import Document, DocumentMappingType, Revision, Locale
from kitsune.wiki.config import (HOW_TO_CATEGORY, TROUBLESHOOTING_CATEGORY,
                                 TEMPLATES_CATEGORY)


@cronjobs.register
def rebuild_kb():
    # If rebuild on demand switch is on, do nothing.
    if waffle.switch_is_active('wiki-rebuild-on-demand'):
        return

    tasks.rebuild_kb()


@cronjobs.register
def reindex_kb():
    """Reindex wiki_document."""
    index_task.delay(DocumentMappingType, DocumentMappingType.get_indexable())


@cronjobs.register
def send_weekly_ready_for_review_digest():
    """Sends out the weekly "Ready for review" digest email."""

    @email_utils.safe_translation
    def _send_mail(locale, user, context):
        subject = _('[Reviews Pending] SUMO needs your help!')

        mail = email_utils.make_mail(
            subject=subject,
            text_template='wiki/email/ready_for_review_weekly_digest.ltxt',
            html_template='wiki/email/ready_for_review_weekly_digest.html',
            context_vars=context,
            from_email=settings.TIDINGS_FROM_ADDRESS,
            to_email=user.email)

        email_utils.send_messages([mail])

    # Get the list of revisions ready for review
    categories = (HOW_TO_CATEGORY, TROUBLESHOOTING_CATEGORY,
                  TEMPLATES_CATEGORY)

    revs = Revision.objects.filter(reviewed=None, document__is_archived=False,
                                   document__category__in=categories)

    revs = revs.filter(Q(document__current_revision_id__lt=F('id')) |
                       Q(document__current_revision_id=None))

    locales = revs.values_list('document__locale', flat=True).distinct()
    products = Product.objects.all()

    for l in locales:
        docs = revs.filter(document__locale=l).values_list(
            'document', flat=True).distinct()
        docs = Document.objects.filter(id__in=docs)

        try:
            leaders = Locale.objects.get(locale=l).leaders.all()
            reviewers = Locale.objects.get(locale=l).reviewers.all()
            users = list(chain(leaders, reviewers))
        except ObjectDoesNotExist:
            # Locale does not exist, so skip to the next locale
            continue

        for u in users:
            _send_mail(l, u, {
                'recipient': u,
                'docs': docs,
                'products': products
            })

            statsd.incr('wiki.cron.weekly-digest-mail')
