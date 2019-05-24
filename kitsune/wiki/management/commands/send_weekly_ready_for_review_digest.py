from itertools import chain

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db.models import F, ObjectDoesNotExist, Q
from django.utils.translation import pgettext
from django.utils.translation import ugettext as _
from django_statsd.clients import statsd

from kitsune.products.models import Product
from kitsune.sumo import email_utils
from kitsune.wiki.config import (HOW_TO_CATEGORY, TEMPLATES_CATEGORY,
                                 TROUBLESHOOTING_CATEGORY)
from kitsune.wiki.models import Document, Locale, Revision


class Command(BaseCommand):
    help = 'Sends out the weekly "Ready for review" digest email.'

    def handle(self, **options):

        @email_utils.safe_translation
        def _send_mail(locale, user, context):
            subject = _('[Reviews Pending: %s] SUMO needs your help!') % locale

            mail = email_utils.make_mail(
                subject=subject,
                text_template='wiki/email/ready_for_review_weekly_digest.ltxt',
                html_template='wiki/email/ready_for_review_weekly_digest.html',
                context_vars=context,
                from_email=settings.TIDINGS_FROM_ADDRESS,
                to_email=user.email)

            email_utils.send_messages([mail])

        # Get the list of revisions ready for review
        categories = (HOW_TO_CATEGORY, TROUBLESHOOTING_CATEGORY, TEMPLATES_CATEGORY)

        revs = Revision.objects.filter(
            reviewed=None, document__is_archived=False, document__category__in=categories)

        revs = revs.filter(
            Q(document__current_revision_id__lt=F('id')) |
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
                users = list(set(chain(leaders, reviewers)))
            except ObjectDoesNotExist:
                # Locale does not exist, so skip to the next locale
                continue

            for u in users:
                docs_list = []
                for p in products:
                    product_docs = docs.filter(
                        Q(parent=None, products__in=[p]) |
                        Q(parent__products__in=[p]))
                    if product_docs:
                        docs_list.append(dict(
                            product=pgettext('DB: products.Product.title', p.title),
                            docs=product_docs))

                product_docs = docs.filter(
                    Q(parent=None, products=None) |
                    Q(parent__products=None))

                if product_docs:
                    docs_list.append(dict(product=_('Other products'), docs=product_docs))

                _send_mail(l, u, {
                    'host': Site.objects.get_current().domain,
                    'locale': l,
                    'recipient': u,
                    'docs_list': docs_list,
                    'products': products
                })

                statsd.incr('wiki.cron.weekly-digest-mail')
