from datetime import date

from mock import patch
from nose.tools import eq_

import kpi.cron
from kpi.cron import update_visitors_metric, update_l10n_metric, Webtrends
from kpi.models import Metric, VISITORS_METRIC_CODE, L10N_METRIC_CODE
from kpi.tests import metric_kind
from sumo.tests import TestCase
from wiki.config import MEDIUM_SIGNIFICANCE, TYPO_SIGNIFICANCE
from wiki.tests import document, revision


class UpdateVisitorsTests(TestCase):
    @patch.object(Webtrends, 'visits')
    def test_update_visitors_cron(self, visits):
        """Verify the cron job inserts the right rows."""
        visitor_kind = metric_kind(code=VISITORS_METRIC_CODE, save=True)
        visits.return_value = {'2012-01-13': 42,
                               '2012-01-14': 193,
                               '2012-01-15': 33}

        update_visitors_metric()

        metrics = Metric.objects.filter(kind=visitor_kind)
        eq_(3, len(metrics))
        eq_(42, metrics[0].value)
        eq_(193, metrics[1].value)
        eq_(date(2012, 01, 15), metrics[2].start)

    @patch.object(kpi.cron, '_get_top_docs')
    @patch.object(Webtrends, 'visits_by_locale')
    def test_update_l10n_metric_cron(self, visits_by_locale, _get_top_docs):
        """Verify the cron job creates the correct metric."""
        l10n_kind = metric_kind(code=L10N_METRIC_CODE, save=True)

        # Create the en-US document with an approved revision.
        doc = document(save=True)
        rev = revision(
            document=doc,
            significance=MEDIUM_SIGNIFICANCE,
            is_approved=True,
            is_ready_for_localization=True,
            save=True)

        # Create a new revision with TYPO_SIGNIFICANCE. It shouldn't
        # affect the results.
        revision(
            document=doc,
            significance=TYPO_SIGNIFICANCE,
            is_approved=True,
            is_ready_for_localization=True,
            save=True)

        # Create an es translation that is up to date.
        es_doc = document(parent=doc, locale='es', save=True)
        revision(
            document=es_doc,
            is_approved=True,
            based_on=rev,
            save=True)

        # Create a de translation without revisions.
        document(parent=doc, locale='de', save=True)

        # Mock some calls.
        visits_by_locale.return_value = {
            'en-US': 100,
            'de': 20,
            'es': 10,
            'fr': 10,
        }
        _get_top_docs.return_value = [doc]

        # Run it and verify results. Values sould be 25% (1/1 * 10/40).
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(25, metrics[0].value)
