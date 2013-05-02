import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test.utils import override_settings

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from products.tests import product
from questions.models import Question, QuestionVote, AnswerVote, Answer
from questions.tests import answer, question
from questions.views import parse_troubleshooting
from search.tests.test_es import ElasticTestCase
from sumo.helpers import urlparams
from sumo.tests import (get, MobileTestCase, LocalizingClient, TestCase,
                        eq_msg)
from sumo.urlresolvers import reverse
from topics.tests import topic
from users.tests import user
from wiki.tests import document, revision


class AAQTests(ElasticTestCase):
    fixtures = ['users.json']
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

    def test_search_suggestions_questions(self):
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

    def test_search_suggestion_question_age(self):
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

    def test_search_suggestion_questions_locale(self):
        """Verifies the right languages show up in search suggestions."""
        topic(title='Fix problems', slug='fix-problems', save=True)
        p = product(slug=u'firefox', save=True)

        q1 = question(title='question cupcakes?', save=True, locale='en-US')
        q1.products.add(p)
        q2 = question(title='question donuts?', save=True, locale='en-US')
        q2.products.add(p)
        q3 = question(title='question pies?', save=True, locale='pt-BR')
        q3.products.add(p)
        q4 = question(title='question pastries?', save=True, locale='de')
        q4.products.add(p)

        self.refresh()

        def sub_test(locale, *titles):
            url = urlparams(reverse('questions.aaq_step4',
                                    args=['desktop', 'fix-problems'],
                                    locale=locale),
                            search='question')
            response = self.client.get(url, follow=True)
            doc = pq(response.content)
            eq_msg(len(doc('.result.question')), len(titles),
                   'Wrong number of results for {0}'.format(locale))
            for substr in titles:
                assert substr in doc('.result.question h3 a').text()

        sub_test('en-US', 'cupcakes?', 'donuts?')
        sub_test('pt-BR', 'cupcakes?', 'donuts?', 'pies?')
        sub_test('de', 'cupcakes?', 'donuts?', 'pastries?')

    def test_search_suggestions_archived_articles(self):
        """Verifies that archived articles aren't shown."""
        topic(title='Fix problems', slug='fix-problems', save=True)
        p = product(slug=u'firefox', save=True)

        d1 = document(title=u'document donut', category=10, save=True)
        d1.products.add(p)
        revision(document=d1, is_approved=True, save=True)

        d2 = document(title=u'document cupcake', category=10, is_archived=True,
                      save=True)
        d2.products.add(p)
        revision(document=d1, is_approved=True, save=True)

        self.refresh()

        url = urlparams(
            reverse('questions.aaq_step4', args=['desktop', 'fix-problems']),
            search='document')

        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        doc = pq(response.content)
        eq_(len(doc('.result.document')), 1)
        assert 'donut' in doc('.result.document h3 a').text()
        assert 'cupcake' not in doc('.result.document h3 a').text()

    def test_ratelimit(self):
        """Make sure posting new questions is ratelimited"""
        data = {'title': 'A test question',
                'content': 'I have this question that I hope...',
                'sites_affected': 'http://example.com',
                'ff_version': '3.6.6',
                'os': 'Intel Mac OS X 10.6',
                'plugins': '* Shockwave Flash 10.1 r53',
                'useragent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X '
                             '10.6; en-US; rv:1.9.2.6) Gecko/20100625 '
                             'Firefox/3.6.6'}
        topic(title='Fix problems', slug='fix-problems', save=True)
        url = urlparams(
            reverse('questions.aaq_step5', args=['desktop', 'fix-problems']),
            search='A test question')

        self.client.login(username='jsocol', password='testpass')

        for i in range(0, 5):
            self.client.post(url, data, follow=True)

        response = self.client.post(url, data, follow=True)
        eq_(403, response.status_code)


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


class TroubleshootingParsingTests(TestCase):

    def test_empty_troubleshooting_info(self):
        """Test a troubleshooting value that is valid JSON, but junk.
        This should trigger the parser to return None, which should not
        cause a 500.
        """
        q = question(save=True)
        q.add_metadata(troubleshooting='{"foo": "bar"}')

        # This case should not raise an error.
        response = get(self.client, 'questions.answers', args=[q.id])
        eq_(200, response.status_code)

    def test_weird_list_troubleshooting_info(self):
        """Test the corner case in which 'modifiedPReferences' is in a
        list in troubleshooting data. This is weird, but caused a bug."""
        q = question(save=True)
        q.add_metadata(troubleshooting='["modifiedPreferences"]')

        # This case should not raise an error.
        response = get(self.client, 'questions.answers', args=[q.id])
        eq_(200, response.status_code)

    def test_string_keys_troubleshooting(self):
        """Test something that looks like troubleshooting data, but
        isn't formatted quite right. The parser should return None to
        indicate that something isn't right."""
        troubleshooting = '''{
            "accessibility": {
                "isActive": true
            },
            "application": {
                "name": "Firefox",
                "supportURL": "Some random url.",
                "userAgent": "A user agent.",
                "version": "42.2"
            },
            "extensions": [],
            "graphics": "This really should not be a string."
            "javaScript": {},
            "modifiedPreferences": {},
            "userJS": {
                "exists": False
            }
        }'''

        assert parse_troubleshooting(troubleshooting) is None

    def test_troubleshooting_parser(self):
        """Test that the troubleshooting parser likes good data."""
        troubleshooting = '''
            {
                "accessibility": {
                    "isActive": true
                },
                "application": {
                    "name": "Firefox",
                    "supportURL": "Some random url.",
                    "userAgent": "A user agent.",
                    "version": "42.2"
                },
                "extensions": [],
                "graphics": {},
                "javaScript": {},
                "modifiedPreferences": {},
                "userJS": {
                    "exists": false
                }
            }'''

        assert parse_troubleshooting(troubleshooting) is not None


class TestQuestionList(TestCase):

    @override_settings(AAQ_LOCALES=['en-US', 'pt-BR'])
    def test_locale_filter(self):
        """Only questions for the current locale should be shown on the
        questions front page for AAQ locales."""

        eq_(Question.objects.count(), 0)
        topic(title='Fix problems', slug='fix-problems', save=True)
        p = product(slug=u'firefox', save=True)

        q1 = question(title='question cupcakes?', save=True, locale='en-US')
        q1.products.add(p)
        q2 = question(title='question donuts?', save=True, locale='en-US')
        q2.products.add(p)
        q3 = question(title='question pies?', save=True, locale='pt-BR')
        q3.products.add(p)
        q4 = question(title='question pastries?', save=True, locale='de')
        q4.products.add(p)

        def sub_test(locale, *titles):
            url = urlparams(reverse('questions.questions', locale=locale))
            response = self.client.get(url, follow=True)
            doc = pq(response.content)
            eq_msg(len(doc('section[id^=question]')), len(titles),
                   'Wrong number of results for {0}'.format(locale))
            for substr in titles:
                assert substr in doc('.questions section .content h2 a').text()

        # en-US and pt-BR are both in AAQ_LOCALES, so should be filtered.
        sub_test('en-US', 'cupcakes?', 'donuts?')
        sub_test('pt-BR', 'pies?')
        # de is not in AAQ_LOCALES, so should show en-US, but not pt-BR
        sub_test('de', 'cupcakes?', 'donuts?', 'pastries?')


class TestRateLimiting(TestCase):
    client_class = LocalizingClient

    def _check_question_vote(self, q, ignored):
        """Try and vote on `q`. If `ignored` is false, assert the
        request worked. If `ignored` is True, assert the request didn't
        do anything."""
        url = reverse('questions.vote', args=[q.id], locale='en-US')
        votes = QuestionVote.objects.filter(question=q).count()

        res = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(res.status_code, 200)

        data = json.loads(res.content)
        eq_(data.get('ignored', False), ignored)

        if ignored:
            eq_(QuestionVote.objects.filter(question=q).count(), votes)
        else:
            eq_(QuestionVote.objects.filter(question=q).count(), votes + 1)

    def _check_answer_vote(self, q, a, ignored):
        """Try and vote on `a`. If `ignored` is false, assert the
        request worked. If `ignored` is True, assert the request didn't
        do anything."""
        url = reverse('questions.answer_vote', args=[q.id, a.id],
                      locale='en-US')
        votes = AnswerVote.objects.filter(answer=a).count()

        res = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(res.status_code, 200)

        data = json.loads(res.content)
        eq_(data.get('ignored', False), ignored)

        if ignored:
            eq_(AnswerVote.objects.filter(answer=a).count(), votes)
        else:
            eq_(AnswerVote.objects.filter(answer=a).count(), votes + 1)

    def test_question_vote_limit(self):
        """Test that an anonymous user's votes are ignored after 10
        question votes."""
        questions = [question(save=True) for _ in range(11)]

        # The rate limit is 10 per day. So make 10 requests. (0 through 9)
        for i in range(10):
            self._check_question_vote(questions[i], False)

        # Now make another, it should fail.
        self._check_question_vote(questions[10], True)

    def test_answer_vote_limit(self):
        """Test that an anonymous user's votes are ignored after 10
        answer votes."""
        q = question(save=True)
        answers = [answer(question=q, save=True) for _ in range(11)]

        # The rate limit is 10 per day. So make 10 requests. (0 through 9)
        for i in range(10):
            self._check_answer_vote(q, answers[i], False)

        # Now make another, it should fail.
        self._check_answer_vote(q, answers[10], True)

    def test_question_vote_logged_in(self):
        """This exhausts the rate limit, then logs in, and exhausts it
        again."""
        questions = [question(save=True) for _ in range(11)]
        u = user(password='testpass', save=True)

        # The rate limit is 10 per day. So make 10 requests. (0 through 9)
        for i in range(10):
            self._check_question_vote(questions[i], False)
        # The rate limit has been hit, so this fails.
        self._check_question_vote(questions[10], True)

        # Login.
        self.client.login(username=u.username, password='testpass')
        for i in range(10):
            self._check_question_vote(questions[i], False)

        # Now the user has hit the rate limit too, so this should fail.
        self._check_question_vote(questions[10], True)

        # Logging out out won't help
        self.client.logout()
        self._check_question_vote(questions[10], True)

    def test_answer_vote_logged_in(self):
        """This exhausts the rate limit, then logs in, and exhausts it
        again."""
        q = question(save=True)
        answers = [answer(question=q, save=True) for _ in range(12)]
        u = user(password='testpass', save=True)

        # The rate limit is 10 per day. So make 10 requests. (0 through 9)
        for i in range(10):
            self._check_answer_vote(q, answers[i], False)
        # The ratelimit has been hit, so the next request will fail.
        self._check_answer_vote(q, answers[11], True)

        # Login.
        self.client.login(username=u.username, password='testpass')
        for i in range(10):
            self._check_answer_vote(q, answers[i], False)

        # Now the user has hit the rate limit too, so this should fail.
        self._check_answer_vote(q, answers[10], True)

        # Logging out out won't help
        self.client.logout()
        self._check_answer_vote(q, answers[11], True)

    def test_answers_limit(self):
        """Only four answers per minute can be posted."""
        # Login
        u = user(password='testpass', save=True)
        self.client.login(username=u.username, password='testpass')

        q = question(save=True)
        content = 'lorem ipsum dolor sit amet'
        url = reverse('questions.reply', args=[q.id])
        for i in range(7):
            response = self.client.post(url, {'content': content})

        eq_(4, Answer.uncached.count())


class TestStats(ElasticTestCase):
    client_class = LocalizingClient

    def test_stats(self):
        """Tests questions/stats view"""
        t = topic(title='Websites', slug='websites', save=True)

        q = question(
            title=u'cupcakes',
            content=u'Cupcakes rock!',
            created=datetime.now() - timedelta(days=1),
            save=True)
        q.topics.add(t)
        q.save()

        self.refresh()

        response = self.client.get(reverse('questions.stats'))
        eq_(200, response.status_code)

        # If there's histogram data, this is probably good enough to
        # denote its existence.
        assert ' data-graph="[' in response.content
