from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from kitsune.products.models import Version
from kitsune.products.tests import ProductFactory


class SyncProductVersionsTests(TestCase):
    def setUp(self):
        self.firefox = ProductFactory(slug="firefox", title="Firefox")
        self.firefox_enterprise = ProductFactory(
            slug="firefox-enterprise", title="Firefox for Enterprise"
        )
        self.mobile = ProductFactory(slug="mobile", title="Firefox for Android")
        self.ios = ProductFactory(slug="ios", title="Firefox for iOS")
        self.thunderbird = ProductFactory(slug="thunderbird", title="Thunderbird")

    def _mock_product_details(self):
        """Mock the product_details module with test data."""
        mock_pd = mock.Mock()

        # Firefox versions data
        mock_pd.firefox_versions = {
            "LATEST_FIREFOX_VERSION": "143.0.4",
            "FIREFOX_ESR": "140.3.1esr",
            "FIREFOX_ESR115": "115.20.0esr",
        }

        # Firefox history data (major releases)
        mock_pd.firefox_history_major_releases = {
            "140.0": "2024-10-29",
            "141.0": "2024-11-26",
            "142.0": "2025-01-07",
            "143.0": "2025-02-04",
        }

        # Mobile versions data
        mock_pd.mobile_versions = {
            "version": "143.0",
        }

        # Thunderbird versions data
        mock_pd.thunderbird_versions = {
            "LATEST_THUNDERBIRD_VERSION": "128.5.0",
            "THUNDERBIRD_ESR": "128.5.0esr",
        }

        # Thunderbird history data
        mock_pd.thunderbird_history_major_releases = {
            "125.0": "2024-03-19",
            "126.0": "2024-04-16",
            "127.0": "2024-05-14",
            "128.0": "2024-06-11",
        }

        return mock_pd

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_sync_firefox_versions(self, mock_product_details):
        """Test syncing Firefox versions from product-details."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        out = StringIO()
        call_command("sync_product_versions", "--product=firefox", stdout=out)

        # Check that versions were created
        versions = Version.objects.filter(product=self.firefox).order_by("slug")
        self.assertGreater(versions.count(), 0)

        # Check specific versions exist
        v140 = Version.objects.get(product=self.firefox, slug="fx140")
        self.assertEqual(v140.name, "Version 140")
        self.assertEqual(v140.min_version, 140.0)
        self.assertEqual(v140.max_version, 141.0)

        v143 = Version.objects.get(product=self.firefox, slug="fx143")
        self.assertEqual(v143.name, "Version 143")
        self.assertEqual(v143.min_version, 143.0)
        self.assertEqual(v143.max_version, 144.0)
        self.assertTrue(v143.default)

        # ESR versions should NOT be created under Firefox product
        esr_versions = Version.objects.filter(product=self.firefox, slug__endswith="-esr")
        self.assertEqual(esr_versions.count(), 0)

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_sync_firefox_enterprise_versions(self, mock_product_details):
        """Test syncing Firefox for Enterprise versions (ESR only)."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        out = StringIO()
        call_command("sync_product_versions", "--product=firefox-enterprise", stdout=out)

        # Check that ESR versions were created under Firefox for Enterprise
        # Should have current ESR versions from esr_keys
        esr140 = Version.objects.get(product=self.firefox_enterprise, slug="fx140-esr")
        self.assertEqual(esr140.name, "Version 140 ESR")
        self.assertTrue(esr140.visible)

        esr115 = Version.objects.get(product=self.firefox_enterprise, slug="fx115-esr")
        self.assertEqual(esr115.name, "Version 115 ESR")
        self.assertTrue(esr115.visible)

        # Should also have historical ESR versions from esr_major_versions
        esr_versions = Version.objects.filter(
            product=self.firefox_enterprise, slug__endswith="-esr"
        )
        # Should have at least the ones in esr_major_versions list
        # [52, 60, 68, 78, 91, 102, 115, 128, 140]
        self.assertGreaterEqual(esr_versions.count(), 9)

        # Regular versions should NOT be created for Firefox for Enterprise (ESR only)
        regular_versions = Version.objects.filter(product=self.firefox_enterprise).exclude(
            slug__endswith="-esr"
        )
        self.assertEqual(regular_versions.count(), 0)

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_sync_mobile_versions(self, mock_product_details):
        """Test syncing Firefox for Android versions."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        out = StringIO()
        call_command("sync_product_versions", "--product=mobile", stdout=out)

        # Check that versions were created
        versions = Version.objects.filter(product=self.mobile)
        self.assertGreater(versions.count(), 0)

        # Check latest version
        v143 = Version.objects.get(product=self.mobile, slug="m143")
        self.assertEqual(v143.name, "Version 143")
        self.assertTrue(v143.default)

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_sync_ios_versions(self, mock_product_details):
        """Test syncing Firefox for iOS versions."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        out = StringIO()
        call_command("sync_product_versions", "--product=ios", stdout=out)

        # Check that versions were created
        versions = Version.objects.filter(product=self.ios)
        self.assertGreater(versions.count(), 0)

        # Check latest version
        v143 = Version.objects.get(product=self.ios, slug="ios143")
        self.assertEqual(v143.name, "Version 143")
        self.assertTrue(v143.default)

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_sync_thunderbird_versions(self, mock_product_details):
        """Test syncing Thunderbird versions."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        out = StringIO()
        call_command("sync_product_versions", "--product=thunderbird", stdout=out)

        # Check that versions were created
        versions = Version.objects.filter(product=self.thunderbird)
        self.assertGreater(versions.count(), 0)

        # Check latest version
        v128 = Version.objects.get(product=self.thunderbird, slug="tb128")
        self.assertEqual(v128.name, "Version 128")
        self.assertTrue(v128.default)

        # Check ESR
        esr128 = Version.objects.get(product=self.thunderbird, slug="tb128-esr")
        self.assertEqual(esr128.name, "Version 128 ESR")
        self.assertTrue(esr128.visible)

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_visibility_rules(self, mock_product_details):
        """Test that only top 10 versions + ESR are visible."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        out = StringIO()
        call_command("sync_product_versions", "--product=firefox", stdout=out)

        visible_regular = Version.objects.filter(product=self.firefox, visible=True).exclude(
            slug__endswith="-esr"
        )

        # Should have top 10 visible (or fewer if less than 10 exist)
        self.assertLessEqual(visible_regular.count(), 10)

        # ESR versions should always be visible
        esr_versions = Version.objects.filter(product=self.firefox, slug__endswith="-esr")
        for esr in esr_versions:
            self.assertTrue(esr.visible)

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_default_version_is_latest(self, mock_product_details):
        """Test that only the latest version is marked as default."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        out = StringIO()
        call_command("sync_product_versions", "--product=firefox", stdout=out)

        default_versions = Version.objects.filter(product=self.firefox, default=True).exclude(
            slug__endswith="-esr"
        )

        # Only one version should be default
        self.assertEqual(default_versions.count(), 1)

        # It should be the latest version
        latest = default_versions.first()
        self.assertEqual(latest.slug, "fx143")

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_dry_run_mode(self, mock_product_details):
        """Test that dry-run mode doesn't modify database."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        initial_count = Version.objects.filter(product=self.firefox).count()

        out = StringIO()
        call_command("sync_product_versions", "--product=firefox", "--dry-run", stdout=out)

        # Count should be unchanged
        final_count = Version.objects.filter(product=self.firefox).count()
        self.assertEqual(initial_count, final_count)

        # Output should indicate dry run
        output = out.getvalue()
        self.assertIn("DRY RUN", output)

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_update_existing_versions(self, mock_product_details):
        """Test that existing versions are updated correctly."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        # Create a version with incorrect values
        Version.objects.create(
            product=self.firefox,
            slug="fx143",
            name="Version 143",
            min_version=100.0,
            max_version=101.0,
            visible=False,
            default=False,
        )

        out = StringIO()
        call_command("sync_product_versions", "--product=firefox", stdout=out)

        # Check that version was updated
        v143 = Version.objects.get(product=self.firefox, slug="fx143")
        self.assertEqual(v143.min_version, 143.0)
        self.assertEqual(v143.max_version, 144.0)
        self.assertTrue(v143.default)

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_sync_all_products(self, mock_product_details):
        """Test syncing all products at once."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        out = StringIO()
        call_command("sync_product_versions", stdout=out)

        # All products should have versions
        self.assertGreater(Version.objects.filter(product=self.firefox).count(), 0)
        self.assertGreater(Version.objects.filter(product=self.firefox_enterprise).count(), 0)
        self.assertGreater(Version.objects.filter(product=self.mobile).count(), 0)
        self.assertGreater(Version.objects.filter(product=self.ios).count(), 0)
        self.assertGreater(Version.objects.filter(product=self.thunderbird).count(), 0)

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_invalid_product(self, mock_product_details):
        """Test that invalid product names are rejected."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        with self.assertRaises(CommandError):
            call_command("sync_product_versions", "--product=invalid")

    @mock.patch("kitsune.products.management.commands.sync_product_versions.product_details")
    def test_archived_product_skipped(self, mock_product_details):
        """Test that archived products are skipped."""
        mock_product_details.configure_mock(**self._mock_product_details().__dict__)

        # Archive Firefox
        self.firefox.is_archived = True
        self.firefox.save()

        out = StringIO()
        call_command("sync_product_versions", "--product=firefox", stdout=out)

        output = out.getvalue()
        self.assertIn("not found or archived", output)

        # Should not create any versions
        self.assertEqual(Version.objects.filter(product=self.firefox).count(), 0)
