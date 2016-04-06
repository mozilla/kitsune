from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import TranslatedRevisionFactory


class LocalizationDashTests(TestCase):
    """Tests for the Localization Dashboard.

    The L10n Dash shares a lot of code with the Contributor Dash, so
    this also covers much of the latter, such as the readout template,
    most of the view mechanics, and the Unreviewed Changes readout
    itself.

    """

    @staticmethod
    def _assert_readout_contains(doc, slug, contents):
        """Assert `doc` contains `contents` within the `slug` readout."""
        html = doc('a#' + slug).closest('details').html()
        assert contents in html, "'" + contents + "' is not in the following: " + html

    def test_render(self):
        """Assert main dash and all the readouts render and don't crash."""
        # Put some stuff in the DB so at least one row renders for each readout:
        unreviewed = TranslatedRevisionFactory(
            document__locale='de',
            reviewed=None,
            is_approved=False,
            is_ready_for_localization=True)

        response = self.client.get(reverse('dashboards.localization', locale='de'), follow=False)
        eq_(200, response.status_code)
        doc = pq(response.content)
        self._assert_readout_contains(doc, 'unreviewed', unreviewed.document.title)

    def test_show_volunteer_button_for_anon(self):
        resp = self.client.get(reverse('dashboards.localization', locale='es'))
        eq_(200, resp.status_code)
        resp_content = pq(resp.content)
        eq_(1, len(resp_content('#get-involved-box')))
        eq_(1, len(resp_content('#get-involved-box .btn-submit')))

    def test_hide_volunteer_button_for_authed(self):
        u1 = UserFactory()
        self.client.login(username=u1.username, password='testpass')
        resp = self.client.get(reverse('dashboards.localization', locale='es'))
        eq_(200, resp.status_code)
        resp_content = pq(resp.content)
        eq_(0, len(resp_content('#get-involved-box')))
