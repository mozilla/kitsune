from datetime import date
from unittest.mock import patch

from google.analytics.data_v1beta.types import DimensionValue, MetricValue, Row

from kitsune.dashboards import LAST_7_DAYS
from kitsune.sumo import googleanalytics
from kitsune.sumo.tests import TestCase


class GoogleAnalyticsTests(TestCase):
    """Tests for the Google Analytics API helper."""

    @patch.object(googleanalytics, "run_report")
    def test_visitors(self, run_report):
        """Test googleanalytics.visitors()."""
        run_report.return_value = (
            Row(
                dimension_values=[DimensionValue(value="20240411")],
                metric_values=[MetricValue(value="23415")],
            ),
            Row(
                dimension_values=[DimensionValue(value="20240414")],
                metric_values=[MetricValue(value="41976")],
            ),
            Row(
                dimension_values=[DimensionValue(value="20240416")],
                metric_values=[MetricValue(value="34657")],
            ),
        )

        result = list(googleanalytics.visitors(date(2024, 4, 11), date(2024, 4, 16)))

        self.assertEqual(6, len(result))
        self.assertEqual(result[0], (date(2024, 4, 11), 23415))
        self.assertEqual(result[1], (date(2024, 4, 12), 0))
        self.assertEqual(result[2], (date(2024, 4, 13), 0))
        self.assertEqual(result[3], (date(2024, 4, 14), 41976))
        self.assertEqual(result[4], (date(2024, 4, 15), 0))
        self.assertEqual(result[5], (date(2024, 4, 16), 34657))

    @patch.object(googleanalytics, "run_report")
    def test_visitors_by_locale(self, run_report):
        """Test googleanalytics.visitors_by_locale()."""
        run_report.return_value = (
            Row(
                dimension_values=[DimensionValue(value="en-US")],
                metric_values=[MetricValue(value="221447")],
            ),
            Row(
                dimension_values=[DimensionValue(value="es")],
                metric_values=[MetricValue(value="24432")],
            ),
            Row(
                dimension_values=[DimensionValue(value="de")],
                metric_values=[MetricValue(value="34657")],
            ),
        )

        visits = googleanalytics.visitors_by_locale(date(2024, 4, 11), date(2024, 4, 20))

        self.assertEqual(3, len(visits))
        self.assertEqual(221447, visits["en-US"])
        self.assertEqual(24432, visits["es"])
        self.assertEqual(34657, visits["de"])

    @patch.object(googleanalytics, "run_report")
    def test_pageviews_by_document(self, run_report):
        """Test googleanalytics.pageviews_by_document()."""
        run_report.return_value = (
            Row(
                dimension_values=[DimensionValue(value="/en-US/kb/doc1-slug")],
                metric_values=[MetricValue(value="1000")],
            ),
            Row(
                dimension_values=[DimensionValue(value="/es/kb/doc2-slug")],
                metric_values=[MetricValue(value="2000")],
            ),
            Row(
                dimension_values=[DimensionValue(value="/de/kb/doc3-slug")],
                metric_values=[MetricValue(value="3000")],
            ),
        )

        result = list(googleanalytics.pageviews_by_document(LAST_7_DAYS))

        self.assertEqual(3, len(result))
        self.assertEqual(result[0], (("en-US", "doc1-slug"), 1000))
        self.assertEqual(result[1], (("es", "doc2-slug"), 2000))
        self.assertEqual(result[2], (("de", "doc3-slug"), 3000))

    @patch.object(googleanalytics, "run_report")
    def test_pageviews_by_question(self, run_report):
        """Test googleanalytics.pageviews_by_question()."""
        run_report.return_value = (
            Row(
                dimension_values=[DimensionValue(value="/en-US/questions/123456")],
                metric_values=[MetricValue(value="1000")],
            ),
            Row(
                dimension_values=[DimensionValue(value="/es/questions/782348")],
                metric_values=[MetricValue(value="2000")],
            ),
            Row(
                dimension_values=[DimensionValue(value="/de/questions/987235")],
                metric_values=[MetricValue(value="3000")],
            ),
        )

        result = list(googleanalytics.pageviews_by_question(LAST_7_DAYS))

        self.assertEqual(3, len(result))
        self.assertEqual(result[0], (123456, 1000))
        self.assertEqual(result[1], (782348, 2000))
        self.assertEqual(result[2], (987235, 3000))

    @patch.object(googleanalytics, "run_report")
    def test_search_clicks_and_impressions(self, run_report):
        """Test googleanalytics.test_search_clicks_and_impressions()."""
        run_report.side_effect = (
            (
                Row(
                    dimension_values=[DimensionValue(value="20240411")],
                    metric_values=[MetricValue(value="10328")],
                ),
                Row(
                    dimension_values=[DimensionValue(value="20240413")],
                    metric_values=[MetricValue(value="9739")],
                ),
            ),
            (
                Row(
                    dimension_values=[DimensionValue(value="20240411")],
                    metric_values=[MetricValue(value="4657")],
                ),
                Row(
                    dimension_values=[DimensionValue(value="20240413")],
                    metric_values=[MetricValue(value="3791")],
                ),
            ),
        )

        result = list(
            googleanalytics.search_clicks_and_impressions(date(2024, 4, 11), date(2024, 4, 13))
        )

        self.assertEqual(3, len(result))
        self.assertEqual(result[0], (date(2024, 4, 11), 4657, 10328))
        self.assertEqual(result[1], (date(2024, 4, 12), 0, 0))
        self.assertEqual(result[2], (date(2024, 4, 13), 3791, 9739))
