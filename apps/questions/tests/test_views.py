from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from products.tests import product
from questions.models import Question
from questions.tests import answer, question
from search.tests.test_es import ElasticTestCase
from sumo.helpers import urlparams
from sumo.tests import MobileTestCase, LocalizingClient, TestCase
from sumo.urlresolvers import reverse
from topics.tests import topic
from users.tests import user
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

        url = urlparams(
            reverse('questions.aaq_step4', args=['desktop', 'd1']),
            search='cupcakes')

        response = self.client.get(url, follow=True)

        assert '<unbleached>' not in response.content

    # TODO: test whether when _search_suggetions fails with a handled
    # error that the user can still ask a question.

    def test_search_suggestions(self):
        """Verifies the view doesn't kick up an HTTP 500"""
        topic(title='Fix problems', slug='fix-problems', save=True)
        p = product(slug=u'firefox', save=True)
        q = question(title=u'CupcakesQuestion cupcakes', save=True)
        q.products.add(p)

        d = document(title=u'CupcakesKB cupcakes', category=10, save=True)
        d.products.add(p)

        rev = revision(document=d, is_approved=True, save=True)

        self.refresh()

        url = urlparams(
            reverse('questions.aaq_step4', args=['desktop', 'fix-problems']),
            search='cupcakes')

        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        assert 'CupcakesQuestion' in response.content
        assert 'CupcakesKB' in response.content

    def test_search_suggestion_age(self):
        """Verifies the view doesn't return old questions."""
        topic(title='Fix problems', slug='fix-problems', save=True)
        p = product(slug=u'firefox', save=True)

        q1 = question(title='Fresh Cupcakes', save=True)
        q1.products.add(p)

        max_age = settings.SEARCH_DEFAULT_MAX_QUESTION_AGE
        too_old = datetime.now() - timedelta(seconds=max_age * 2)
        q2 = question(title='Stale Cupcakes', created=too_old, updated=too_old,
                      save=True)
        q2.products.add(p)

        self.refresh()

        url = urlparams(
            reverse('questions.aaq_step4', args=['desktop', 'fix-problems']),
                    search='cupcakes')

        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        self.assertContains(response, q1.title)
        self.assertNotContains(response, q2.title)


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
        topic(title='Fix problems', slug='fix-problems', save=True)
        url = urlparams(
            reverse('questions.aaq_step5', args=['desktop', 'fix-problems']),
            search='A test question')
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

    def test_aaq_login_form(self):
        """The AAQ authentication forms contain the identifying fields.

        Added this test because it is hard to debug what happened when this
        fields somehow go missing.
        """
        res = self._new_question()
        doc = pq(res.content)
        eq_(1, len(doc('#login-form input[name=login]')))
        eq_(1, len(doc('#register-form input[name=register]')))


class TestQuestionUpdates(TestCase):
    """Tests that questions are only updated in the right cases."""
    client_class = LocalizingClient

    date_format = '%Y%M%d%H%m%S'

    def setUp(self):
        super(TestQuestionUpdates, self).setUp()
        self.u = user(is_superuser=True, save=True)
        self.client.login(username=self.u.username, password='testpass')

        self.q = question(updated=datetime(2012, 7, 9, 9, 0, 0), save=True)
        self.a = answer(question=self.q, save=True)

        # Get the question from the database so we have a consistent level of
        # precision during the test.
        self.q = Question.objects.get(pk=self.q.id)

    def tearDown(self):
        self.client.logout()
        self.u.delete()
        self.q.delete()

    def _request_and_no_update(self, url, req_type='POST', data={}):
        updated = self.q.updated

        if req_type == 'POST':
            self.client.post(url, data, follow=True)
        elif req_type == 'GET':
            self.client.get(url, data, follow=True)
        else:
            raise ValueError('req_type must be either "GET" or "POST"')

        self.q = Question.objects.get(pk=self.q.id)
        eq_(updated.strftime(self.date_format),
            self.q.updated.strftime(self.date_format))

    def test_no_update_edit(self):
        url = urlparams(reverse('questions.edit_question', args=[self.q.id]))
        self._request_and_no_update(url, req_type='POST', data={
                'title': 'A new title.',
                'content': 'Some new content.'
            })

    def test_no_update_solve(self):
        url = urlparams(reverse('questions.solve',
            args=[self.q.id, self.a.id]))
        self._request_and_no_update(url)

    def test_no_update_unsolve(self):
        url = urlparams(reverse('questions.unsolve',
            args=[self.q.id, self.a.id]))
        self._request_and_no_update(url)

    def test_no_update_vote(self):
        url = urlparams(reverse('questions.vote', args=[self.q.id]))
        self._request_and_no_update(url, req_type='POST')

    def test_no_update_lock(self):
        url = urlparams(reverse('questions.lock', args=[self.q.id]))
        self._request_and_no_update(url, req_type='POST')
        # Now unlock
        self._request_and_no_update(url, req_type='POST')

    def test_no_update_tagging(self):
        url = urlparams(reverse('questions.add_tag', args=[self.q.id]))
        self._request_and_no_update(url, req_type='POST', data={
                'tag-name': 'foo'
            })

        url = urlparams(reverse('questions.remove_tag', args=[self.q.id]))
        self._request_and_no_update(url, req_type='POST', data={
                'remove-tag-foo': 1
            })
