import time

from django.urls import reverse

from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory

XSS_TITLE = '<script>alert("kbadge-xss")</script>'
RAW_PAYLOAD = '<script>alert("kbadge-xss")'
ESCAPED_PAYLOAD = "&lt;script&gt;alert("


class BadgeAdminEscapingTests(TestCase):
    def setUp(self):
        self.superuser = UserFactory(is_staff=True, is_superuser=True)
        # Admin requests pass through SUMORefreshIDTokenAdminMiddleware, which forces OIDC
        # re-authentication (a 302) unless the session was created by the OIDC backend and
        # carries an unexpired ID token. Build a session that satisfies both conditions.
        self.client.force_login(self.superuser, backend="kitsune.users.auth.SumoOIDCAuthBackend")
        session = self.client.session
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()

    def test_badge_changelist_escapes_title(self):
        # Exercises the title column and the related_awards_link callable.
        badge = BadgeFactory(title=XSS_TITLE)
        AwardFactory(badge=badge)

        resp = self.client.get(reverse("admin:kbadge_badge_changelist"))

        self.assertEqual(200, resp.status_code)
        self.assertNotContains(resp, RAW_PAYLOAD)
        self.assertContains(resp, ESCAPED_PAYLOAD)

    def test_award_changelist_escapes_badge_title(self):
        # Exercises the Award __str__ column and the badge_link callable, both of
        # which embed the (attacker-controlled) badge title.
        badge = BadgeFactory(title=XSS_TITLE)
        AwardFactory(badge=badge)

        resp = self.client.get(reverse("admin:kbadge_award_changelist"))

        self.assertEqual(200, resp.status_code)
        self.assertNotContains(resp, RAW_PAYLOAD)
        self.assertContains(resp, ESCAPED_PAYLOAD)
