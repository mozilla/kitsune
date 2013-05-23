import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from django.contrib.sites.models import Site

from announcements.tests import announcement
from dashboards.tests import group_dashboard
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from users.tests import user, group, profile
from wiki.config import MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE
from wiki.tests import revision, translated_revision


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
        assert contents in html, \
            "'" + contents + "' is not in the following: " + html

    def test_render(self):
        """Assert main dash and all the readouts render and don't crash."""
        # Put some stuff in the DB so at least one row renders for each
        # readout:
        untranslated = revision(is_approved=True,
                                is_ready_for_localization=True)
        untranslated.save()

        unreviewed = translated_revision(is_ready_for_localization=True)
        unreviewed.save()

        out_of_date = translated_revision(is_approved=True,
                                          is_ready_for_localization=True)
        out_of_date.save()
        major_update = revision(document=out_of_date.document.parent,
                                significance=MAJOR_SIGNIFICANCE,
                                is_approved=True,
                                is_ready_for_localization=True)
        major_update.save()

        needing_updates = translated_revision(is_approved=True,
                                              is_ready_for_localization=True)
        needing_updates.save()
        medium_update = revision(document=needing_updates.document.parent,
                                 significance=MEDIUM_SIGNIFICANCE,
                                 is_ready_for_localization=True)
        medium_update.save()

        response = self.client.get(reverse('dashboards.localization',
                                           locale='de'),
                                   follow=False)
        eq_(200, response.status_code)
        doc = pq(response.content)
        self._assert_readout_contains(doc, 'untranslated',
                                      untranslated.document.title)
        self._assert_readout_contains(doc, 'unreviewed',
                                      unreviewed.document.title)
        self._assert_readout_contains(doc, 'out-of-date',
                                      out_of_date.document.title)
        # TODO: Why does this fail? Is the setup wrong, or is the query?
        # self._assert_readout_contains(doc, 'needing-updates',
        #                               needing_updates.document.title)

    def test_untranslated_detail(self):
        """Assert the whole-page Untranslated Articles view works."""
        # We don't need to test every whole-page view: just one, to
        # make sure the localization_detail template and the view
        # work. All the readouts' querying and formatting methods,
        # including the various template parameters for each
        # individual readout, are exercised by rendering the main,
        # multi-readout page.

        # Put something in the DB so something shows up:
        untranslated = revision(is_approved=True,
                                is_ready_for_localization=True)
        untranslated.save()

        response = self.client.get(reverse('dashboards.localization_detail',
                                           args=['untranslated'],
                                           locale='de'))
        self.assertContains(response, untranslated.document.title)


class GroupLocaleDashTests(TestCase):

    def setUp(self):
        super(GroupLocaleDashTests, self).setUp()
        self.g = group(save=True, name='A group')
        # defaults to a 'de' localization dashboard
        group_dashboard(group=self.g, save=True)

    def test_anonymous_user(self):
        """Checks the locale dashboard doesn't load for an anonymous user."""
        response = self.client.get(reverse('dashboards.group',
                                           args=[self.g.pk], locale='en-US'))
        eq_(302, response.status_code)
        assert '/users/login' in response['location']

    def test_for_user_not_in_group(self):
        """Checks the locale dashboard doesn't load for user not in group."""
        user(username='test', save=True)
        self.client.login(username='test', password='testpass')
        response = self.client.get(reverse('dashboards.group',
                                           args=[self.g.pk], locale='en-US'))
        eq_(404, response.status_code)

    @mock.patch.object(Site.objects, 'get_current')
    def test_for_user_active(self, get_current):
        """Checks the locale dashboard loads for a user associated with it.
        """
        get_current.return_value.domain = 'testserver'
        # Create user/group and add user to group.
        u = user(username='test', save=True)
        u.groups.add(self.g)
        profile(user=u)
        # Create site-wide and group announcements and dashboard.
        announcement().save()
        content = 'stardate 12341'
        announcement(group=self.g, content=content).save()

        # Log in and check response.
        self.client.login(username='test', password='testpass')
        response = self.client.get(reverse('dashboards.group',
                                           args=[self.g.pk]), follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        # The locale dash tab shows up.
        eq_(4, len(doc('#user-nav li')))
        # The locale dash tabs shows up and is active
        eq_(u'A group', doc('#user-nav li.selected').text())
        # The subtitle shows French.
        eq_(u'Deutsch', doc('article h2.subtitle').text())
        # The correct announcement shows up.
        self.assertContains(response, content)
