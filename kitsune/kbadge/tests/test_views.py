from markupsafe import escape

from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class AwardsListTests(TestCase):
    def test_list_empty(self):
        resp = self.client.get(reverse("kbadge.awards_list"), follow=True)
        self.assertEqual(200, resp.status_code)

    def test_list_with_awards(self):
        b = BadgeFactory()
        a1 = AwardFactory(description="A1 AWARD", badge=b)
        a2 = AwardFactory(description="A2 AWARD", badge=b)
        a3 = AwardFactory(description="A3 AWARD", badge=b)

        resp = self.client.get(reverse("kbadge.awards_list"), follow=True)
        self.assertEqual(200, resp.status_code)
        self.assertContains(resp, a1.user.username)
        self.assertContains(resp, a1.get_absolute_url())
        self.assertContains(resp, a2.user.username)
        self.assertContains(resp, a2.get_absolute_url())
        self.assertContains(resp, a3.user.username)
        self.assertContains(resp, a3.get_absolute_url())


class AwardDetailsTests(TestCase):
    def test_details_page(self):
        # This is a just basic test to make sure the template loads.
        a1 = AwardFactory(description="A1 AWARD")

        resp = self.client.get(a1.get_absolute_url(), follow=True)
        self.assertEqual(200, resp.status_code)


class BadgeFieldEscapingTests(TestCase):
    XSS_TITLE = "<img src=x onerror=alert(1)>"
    XSS_DESCRIPTION = "<img src=y onerror=alert(2)>"

    def _assert_escaped(self, resp, payload):
        self.assertEqual(200, resp.status_code)
        # The raw payload must be absent (it would execute), and its escaped
        # form present (confirming the value rendered, just safely).
        self.assertNotContains(resp, payload)
        self.assertContains(resp, escape(payload))

    def test_badges_list_escapes_title(self):
        BadgeFactory(title=self.XSS_TITLE)
        resp = self.client.get(reverse("kbadge.badges_list"), follow=True)
        self._assert_escaped(resp, self.XSS_TITLE)

    def test_badge_detail_escapes_title(self):
        badge = BadgeFactory(title=self.XSS_TITLE)
        self._assert_escaped(
            self.client.get(badge.get_absolute_url(), follow=True), self.XSS_TITLE
        )

    def test_awards_list_escapes_title(self):
        AwardFactory(badge=BadgeFactory(title=self.XSS_TITLE))
        resp = self.client.get(reverse("kbadge.awards_list"), follow=True)
        self._assert_escaped(resp, self.XSS_TITLE)

    def test_award_detail_escapes_title(self):
        award = AwardFactory(badge=BadgeFactory(title=self.XSS_TITLE))
        self._assert_escaped(
            self.client.get(award.get_absolute_url(), follow=True), self.XSS_TITLE
        )

    def test_badge_detail_escapes_description(self):
        badge = BadgeFactory(description=self.XSS_DESCRIPTION)
        self._assert_escaped(
            self.client.get(badge.get_absolute_url(), follow=True), self.XSS_DESCRIPTION
        )

    def test_award_detail_escapes_description(self):
        award = AwardFactory(badge=BadgeFactory(description=self.XSS_DESCRIPTION))
        self._assert_escaped(
            self.client.get(award.get_absolute_url(), follow=True), self.XSS_DESCRIPTION
        )

    def test_title_escaped_in_attribute_context(self):
        # The title also renders inside title="..." attributes, where a double
        # quote would break out without any tag.
        payload = '" onmouseover=alert(1) x="'
        BadgeFactory(title=payload)
        resp = self.client.get(reverse("kbadge.badges_list"), follow=True)
        self._assert_escaped(resp, payload)
