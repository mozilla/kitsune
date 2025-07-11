from unittest.mock import patch

from kitsune.dashboards import LAST_7_DAYS
from kitsune.dashboards.models import WikiDocumentVisits, googleanalytics
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import ApprovedRevisionFactory


class DocumentVisitsTests(TestCase):
    """Tests for the pageview statistics gathering."""

    @patch.object(googleanalytics, "pageviews_by_document")
    def test_visit_count_from_analytics(self, pageviews_by_document):
        """Verify stored visit counts."""
        d1 = ApprovedRevisionFactory(document__slug="doc1-slug").document
        d2 = ApprovedRevisionFactory(document__slug="doc2-slug").document
        d3 = ApprovedRevisionFactory(document__slug="doc3-slüg").document

        pageviews_by_document.return_value = dict(
            row
            for row in (
                (("en-US", d1.slug), 1000),
                (("es", "no-existe"), 150),
                (("en-US", d2.slug), 2000),
                (("en-US", d3.slug), 3000),
                (("de", "nicht-existent"), 350),
            )
        )

        WikiDocumentVisits.reload_period_from_analytics(LAST_7_DAYS)

        self.assertEqual(3, WikiDocumentVisits.objects.count())
        wdv1 = WikiDocumentVisits.objects.get(document=d1)
        self.assertEqual(1000, wdv1.visits)
        self.assertEqual(LAST_7_DAYS, wdv1.period)
        wdv2 = WikiDocumentVisits.objects.get(document=d2)
        self.assertEqual(2000, wdv2.visits)
        self.assertEqual(LAST_7_DAYS, wdv2.period)
        wdv3 = WikiDocumentVisits.objects.get(document=d3)
        self.assertEqual(3000, wdv3.visits)
        self.assertEqual(LAST_7_DAYS, wdv2.period)
