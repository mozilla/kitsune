from django.test import RequestFactory

from kitsune.announcements.utils import detect_platform_from_user_agent
from kitsune.sumo.tests import TestCase


class PlatformDetectionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_windows_11_client_hints(self):
        """Test Windows 11 detection using client hints."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"Windows"'
        request.META['HTTP_SEC_CH_UA_PLATFORM_VERSION'] = '"14.0.0"'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["win11"])

    def test_windows_10_client_hints(self):
        """Test Windows 10 detection using client hints."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"Windows"'
        request.META['HTTP_SEC_CH_UA_PLATFORM_VERSION'] = '"10.0.0"'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["win10"])

    def test_windows_11_higher_version(self):
        """Test Windows 11 detection with version 15+ (future versions)."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"Windows"'
        request.META['HTTP_SEC_CH_UA_PLATFORM_VERSION'] = '"15.1.2"'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["win11"])

    def test_windows_fallback_to_user_agent(self):
        """Test fallback to user agent when client hints unavailable."""
        request = self.factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["win10", "win11"])  # Returns both for uncertainty

    def test_macos_client_hints(self):
        """Test macOS detection using client hints."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"macOS"'
        request.META['HTTP_SEC_CH_UA_PLATFORM_VERSION'] = '"13.0.0"'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["mac"])

    def test_linux_client_hints(self):
        """Test Linux detection using client hints."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"Linux"'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["linux"])

    def test_android_client_hints(self):
        """Test Android detection using client hints."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"Android"'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["android"])

    def test_ios_client_hints(self):
        """Test iOS detection using client hints (mapped to mac)."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"iOS"'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["mac"])  # iOS mapped to mac for now

    def test_invalid_platform_version(self):
        """Test handling of invalid platform version strings."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"Windows"'
        request.META['HTTP_SEC_CH_UA_PLATFORM_VERSION'] = '"invalid.version"'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["win10", "win11"])  # Falls back to user agent

    def test_empty_platform_version(self):
        """Test handling of empty platform version."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"Windows"'
        request.META['HTTP_SEC_CH_UA_PLATFORM_VERSION'] = '""'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["win10", "win11"])  # Falls back to user agent

    def test_no_client_hints_fallback_to_ua(self):
        """Test complete fallback to user agent when no client hints present."""
        request = self.factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["mac"])

    def test_no_user_agent_returns_web(self):
        """Test fallback to web when no user agent available."""
        request = self.factory.get('/')

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["web"])

    def test_windows_old_version_client_hints(self):
        """Test Windows with very old version returns both platforms."""
        request = self.factory.get('/')
        request.META['HTTP_SEC_CH_UA_PLATFORM'] = '"Windows"'
        request.META['HTTP_SEC_CH_UA_PLATFORM_VERSION'] = '"6.1.0"'  # Windows 7 era

        platforms = detect_platform_from_user_agent(request)
        self.assertEqual(platforms, ["win10", "win11"])  # Returns both for uncertainty
