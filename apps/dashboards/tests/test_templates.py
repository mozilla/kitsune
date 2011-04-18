from nose.tools import eq_
from pyquery import PyQuery as pq

from django.contrib.auth.models import User

from announcements.tests import announcement
from dashboards.tests import group_dashboard
from forums.models import Post
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from users.tests import user, group
from wiki.models import MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE
from wiki.tests import revision, translated_revision


class LocalizationDashTests(TestCase):
    """Tests for the Localization Dashboard.

    The L10n Dash shares a lot of code with the Contributor Dash, so this also
    covers much of the latter, such as the readout template, most of the view
    mechanics, and the Unreviewed Changes readout itself.

    """

    fixtures = ['users.json']

    @staticmethod
    def _assert_readout_contains(doc, slug, contents):
        """Assert `doc` contains `contents` within the `slug` readout."""
        html = doc('a#' + slug).closest('details').html()
        assert contents in html, \
            "'" + contents + "' is not in the following: " + html

    def test_render(self):
        """Assert the main dash and all the readouts render and don't crash."""
        # Put some stuff in the DB so at least one row renders for each
        # readout:
        untranslated = revision(is_approved=True)
        untranslated.save()

        unreviewed = translated_revision()
        unreviewed.save()

        out_of_date = translated_revision(is_approved=True)
        out_of_date.save()
        major_update = revision(document=out_of_date.document.parent,
                                significance=MAJOR_SIGNIFICANCE,
                                is_approved=True)
        major_update.save()

        needing_updates = translated_revision(is_approved=True)
        needing_updates.save()
        medium_update = revision(document=needing_updates.document.parent,
                                significance=MEDIUM_SIGNIFICANCE)
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
        # TODO: Why do these fail? The query doesn't return the rows set up
        # above. Is the setup wrong, or is the query?
        # self._assert_readout_contains(doc, 'out-of-date',
        #                               out_of_date.document.title)
        # self._assert_readout_contains(doc, 'needing-updates',
        #                               needing_updates.document.title)

    def test_untranslated_detail(self):
        """Assert the whole-page Untranslated Articles view works."""
        # We don't need to test every whole-page view: just one, to make sure
        # the localization_detail template and the view work. All the readouts'
        # querying and formatting methods, including the various template
        # parameters for each individual readout, are exercised by rendering
        # the main, multi-readout page.

        # Put something in the DB so something shows up:
        untranslated = revision(is_approved=True)
        untranslated.save()

        response = self.client.get(reverse('dashboards.localization_detail',
                                           args=['untranslated'],
                                           locale='de'))
        self.assertContains(response, untranslated.document.title)


class ContributorForumDashTests(TestCase):
    fixtures = ['users.json', 'posts.json', 'forums_permissions.json']

    def setUp(self):
        super(ContributorForumDashTests, self).setUp()
        self.client.login(username='jsocol', password='testpass')

    def test_no_activity(self):
        """Test the page with no activity."""
        response = self.client.get(reverse('dashboards.review'), follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('No recent activity.', doc('#forums-dashboard p').text())

    def test_with_activity(self):
        """Test the page with some activity."""
        # Add a reply
        post = Post(thread_id=4, content='lorem ipsum', author_id=118577)
        post.save()
        # Verify activity on the page
        response = self.client.get(reverse('dashboards.review'), follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('ol.actions li')))


class AnnouncementForumDashTests(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(AnnouncementForumDashTests, self).setUp()
        self.client.login(username='jsocol', password='testpass')
        self.creator = User.objects.all()[0]

    def test_active(self):
        """Active announcement shows."""
        announcement(creator=self.creator).save()

        response = self.client.get(reverse('dashboards.review'), follow=True)
        self.assertContains(response, 'stardate 43124.5')

    def test_no_announcements(self):
        """Template renders with no announcements."""
        response = self.client.get(reverse('dashboards.review'), follow=True)
        doc = pq(response.content)
        assert not len(doc('ol.announcements'))


class GroupLocaleDashTests(TestCase):

    def test_anonymous_user(self):
        """Checks the locale dashboard loads for an anonymous user."""
        response = self.client.get(reverse('dashboards.group_locale',
                                           locale='de', args=['fr']))
        eq_(200, response.status_code)
        doc = pq(response.content)
        # The locale dash tab does not show up.
        eq_(3, len(doc('#doc-tabs li')))
        # The subtitle shows French.
        eq_(u'Fran\xe7ais', doc('#main h2.subtitle').text())

    def test_for_user_active(self):
        """Checks the locale dashboard loads for a user associated with it."""
        # Create user/group and add user to group.
        u = user(username='test', save=True)
        g = group(save=True)
        u.groups.add(g)
        # Create site-wide and group announcements and dashboard.
        announcement().save()
        content = 'stardate 12341'
        announcement(group=g, content=content).save()
        group_dashboard(save=True)  # defaults to a 'de' localization dashboard

        # Log in and check response.
        self.client.login(username='test', password='testpass')
        response = self.client.get(reverse('dashboards.group_locale',
                                           locale='fr', args=['de']))
        eq_(200, response.status_code)
        doc = pq(response.content)
        # The locale dash tab shows up.
        eq_(4, len(doc('#doc-tabs li')))
        # The locale dash tabs shows up and is active
        eq_(u'Deutsch', doc('#doc-tabs li.active').text())
        # The subtitle shows French.
        eq_(u'Deutsch', doc('#main h2.subtitle').text())
        # The correct announcement shows up.
        self.assertContains(response, content)
