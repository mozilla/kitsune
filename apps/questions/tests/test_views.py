from django.contrib.auth.models import User
from django.contrib.sites.models import Site

import mock
from nose.tools import eq_

from questions.models import Question
from questions.tests import question
from search.tests.test_es import ElasticTestCase
from sumo.helpers import urlparams
from sumo.urlresolvers import reverse
from sumo.tests import MobileTestCase, LocalizingClient
from wiki.tests import document, revision


class AAQTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_bleaching(self):
        """Tests whether summaries are bleached"""
        q = question(
            title=u'cupcakes',
            content=u'<unbleached>Cupcakes are the best</unbleached',
            save=True)
        q.tags.add(u'desktop')
        q.save()
        self.refresh()

        url = urlparams(reverse('questions.new_question'),
                        product='desktop',
                        category='d1',
                        search='cupcakes')

        response = self.client.get(url, follow=True)

        assert '<unbleached>' not in response.content

    # TODO: test whether when _search_suggetions fails with a handled
    # error that the user can still ask a question.

    def test_search_suggestions(self):
        """Verifies the view doesn't kick up an HTTP 500"""
        q = question(title=u'CupcakesQuestion cupcakes', save=True)
        q.tags.add(u'desktop')
        q.save()

        d = document(title=u'CupcakesKB cupcakes', category=10, save=True)
        d.tags.add(u'desktop')
        d.save()

        rev = revision(document=d, is_approved=True)
        rev.save()

        self.refresh()

        url = urlparams(reverse('questions.new_question'),
                        product='desktop',
                        category='d1',
                        search='cupcakes')

        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        assert 'CupcakesQuestion' in response.content
        assert 'CupcakesKB' in response.content


class MobileAAQTests(MobileTestCase):
    fixtures = ['users.json', 'questions.json']
    client_class = LocalizingClient
    data = {'title': 'A test question',
            'content': 'I have this question that I hope...',
            'sites_affected': 'http://example.com',
            'ff_version': '3.6.6',
            'os': 'Intel Mac OS X 10.6',
            'plugins': '* Shockwave Flash 10.1 r53',
            'useragent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X '
                         '10.6; en-US; rv:1.9.2.6) Gecko/20100625 '
                         'Firefox/3.6.6'}

    def _new_question(self, post_it=False):
        """Post a new question and return the response."""
        url = urlparams(reverse('questions.new_question'),
                        product='desktop', category='d1',
                        search='A test question', showform=1)
        if post_it:
            return self.client.post(url, self.data, follow=True)
        return self.client.get(url, follow=True)

    def test_logged_out(self):
        """New question is posted through mobile."""
        response = self._new_question()
        eq_(200, response.status_code)
        self.assertTemplateUsed(response,
                                'questions/mobile/new_question_login.html')

    @mock.patch.object(Site.objects, 'get_current')
    def test_logged_in_get(self, get_current):
        """New question is posted through mobile."""
        get_current.return_value.domain = 'testserver'
        self.client.login(username='jsocol', password='testpass')
        response = self._new_question()
        eq_(200, response.status_code)
        self.assertTemplateUsed(response,
                                'questions/mobile/new_question.html')

    @mock.patch.object(Site.objects, 'get_current')
    def test_logged_in_post(self, get_current):
        """New question is posted through mobile."""
        get_current.return_value.domain = 'testserver'
        self.client.login(username='jsocol', password='testpass')
        response = self._new_question(post_it=True)
        eq_(200, response.status_code)
        assert Question.objects.filter(title='A test question')

    @mock.patch.object(Site.objects, 'get_current')
    def test_aaq_new_question_inactive(self, get_current):
        """New question is posted through mobile."""
        get_current.return_value.domain = 'testserver'
        # Log in first.
        self.client.login(username='jsocol', password='testpass')
        # Then become inactive.
        u = User.objects.get(username='jsocol')
        u.is_active = False
        u.save()

        response = self._new_question(post_it=True)
        eq_(200, response.status_code)
        self.assertTemplateUsed(response,
                                'questions/mobile/confirm_email.html')
