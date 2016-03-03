import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.test.utils import override_settings

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.flagit.models import FlaggedObject
from kitsune.products.tests import ProductFactory
from kitsune.questions.models import (
    Question, QuestionVote, AnswerVote, Answer, QuestionLocale)
from kitsune.questions.tests import (
    AnswerFactory, QuestionFactory, TestCaseBase, QuestionLocaleFactory)
from kitsune.questions.views import parse_troubleshooting
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import (
    get, MobileTestCase, LocalizingClient, eq_msg, set_waffle_flag, template_used)
from kitsune.sumo.urlresolvers import reverse
from kitsune.products.tests import TopicFactory
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory, add_permission
from kitsune.wiki.tests import DocumentFactory, RevisionFactory


class AAQTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_bleaching(self):
        """Tests whether summaries are bleached"""
        p = ProductFactory(slug=u'firefox')
        l = QuestionLocale.objects.get(locale=settings.LANGUAGE_CODE)
        p.questions_locales.add(l)
        TopicFactory(title='Fix problems', slug='fix-problems', product=p)
        QuestionFactory(
            product=p,
            title=u'CupcakesQuestion cupcakes',
            content=u'cupcakes are best with <unbleached>flour</unbleached>')

        self.refresh()

        url = urlparams(
            reverse('questions.aaq_step4', args=['desktop', 'fix-problems']),
            search='cupcakes')

        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        assert 'CupcakesQuestion' in response.content
        assert '<unbleached>' not in response.content
        assert 'cupcakes are best with' in response.content

    # TODO: test whether when _search_suggetions fails with a handled
    # error that the user can still ask a question.

    def test_search_suggestions_questions(self):
        """Verifies the view doesn't kick up an HTTP 500"""
        p = ProductFactory(slug=u'firefox')
        l = QuestionLocale.objects.get(locale=settings.LANGUAGE_CODE)
        p.questions_locales.add(l)
        TopicFactory(title='Fix problems', slug='fix-problems', product=p)
        q = QuestionFactory(product=p, title=u'CupcakesQuestion cupcakes')

        d = DocumentFactory(title=u'CupcakesKB cupcakes', category=10)
        d.products.add(p)

        RevisionFactory(document=d, is_approved=True)

        self.refresh()

        url = urlparams(
            reverse('questions.aaq_step4', args=['desktop', 'fix-problems']),
            search='cupcakes')

        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        assert 'CupcakesQuestion' in response.content
        assert 'CupcakesKB' in response.content

        # Verify that archived articles and questions aren't shown...
        # Archive both and they shouldn't appear anymore.
        q.is_archived = True
        q.save()
        d.is_archived = True
        d.save()

        self.refresh()

        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        assert 'CupcakesQuestion' not in response.content
        assert 'CupcakesKB' not in response.content

    def test_search_suggestion_questions_locale(self):
        """Verifies the right languages show up in search suggestions."""
        QuestionLocaleFactory(locale='de')

        p = ProductFactory(slug=u'firefox')

        for l in QuestionLocale.objects.all():
            p.questions_locales.add(l)

        TopicFactory(title='Fix problems', slug='fix-problems', product=p)

        QuestionFactory(title='question cupcakes?', product=p, locale='en-US')
        QuestionFactory(title='question donuts?', product=p, locale='en-US')
        QuestionFactory(title='question pies?', product=p, locale='pt-BR')
        QuestionFactory(title='question pastries?', product=p, locale='de')

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
        p = ProductFactory(slug='firefox')
        l = QuestionLocale.objects.get(locale=settings.LANGUAGE_CODE)
        p.questions_locales.add(l)
        TopicFactory(slug='fix-problems', product=p)
        url = urlparams(
            reverse('questions.aaq_step5', args=['desktop', 'fix-problems']),
            search='A test question')

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

        for i in range(0, 5):
            self.client.post(url, data, follow=True)

        response = self.client.post(url, data, follow=True)
        eq_(403, response.status_code)

    def test_first_step(self):
        """Make sure the first step doesn't blow up

        Oddly, none of the other tests cover this simple case.
        """
        url = reverse('questions.aaq_step1')
        res = self.client.get(url)
        eq_(200, res.status_code)

    def test_redirect_bad_locales(self):
        """Non-AAQ locales should redirect."""
        url_fr = reverse('questions.aaq_step1', locale='fr')
        url_en = reverse('questions.aaq_step1', locale='en-US')
        res = self.client.get(url_fr)
        eq_(302, res.status_code)
        # This has some http://... stuff at the beginning. Ignore that.
        assert res['location'].endswith(url_en)

    @override_settings(WIKI_DEFAULT_LANGUAGE='fr')
    def test_no_redirect_english(self):
        """The default language should never redirect, even if it isn't an AAQ language."""
        """Non-AAQ locales should redirect."""
        url_fr = reverse('questions.aaq_step1', locale='fr')
        res = self.client.get(url_fr)
        eq_(200, res.status_code)

    def test_redirect_locale_not_enabled(self):
        """AAQ should redirect for products with questions disabled for the
        current locale"""
        url_fi = reverse('questions.aaq_step1', locale='fi')
        res = self.client.get(url_fi)
        eq_(200, res.status_code)

        p = ProductFactory(slug='firefox')

        url_fi = reverse('questions.aaq_step2', locale='fi', args=['desktop'])
        url_en = reverse('questions.aaq_step2', locale='en-US',
                         args=['desktop'])
        res = self.client.get(url_fi)
        eq_(302, res.status_code)
        assert res['location'].endswith(url_en)

        l = QuestionLocale.objects.get(locale='fi')
        p.questions_locales.add(l)
        res = self.client.get(url_fi)
        eq_(200, res.status_code)


class MobileAAQTests(MobileTestCase):
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
        p = ProductFactory(slug='mobile')
        l = QuestionLocale.objects.get(locale=settings.LANGUAGE_CODE)
        p.questions_locales.add(l)
        t = TopicFactory(slug='fix-problems', product=p)
        url = urlparams(
            reverse('questions.aaq_step5', args=[p.slug, t.slug]),
            search='A test question')
        if post_it:
            return self.client.post(url, self.data, follow=True)
        return self.client.get(url, follow=True)

    def test_logged_out(self):
        """New question is posted through mobile."""
        response = self._new_question()
        eq_(200, response.status_code)
        assert template_used(response, 'questions/mobile/new_question_login.html')

    @mock.patch.object(Site.objects, 'get_current')
    def test_logged_in_get(self, get_current):
        """New question is posted through mobile."""
        get_current.return_value.domain = 'testserver'

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

        response = self._new_question()
        eq_(200, response.status_code)
        assert template_used(response, 'questions/mobile/new_question.html')

    @mock.patch.object(Site.objects, 'get_current')
    def test_logged_in_post(self, get_current):
        """New question is posted through mobile."""
        get_current.return_value.domain = 'testserver'

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

        response = self._new_question(post_it=True)
        eq_(200, response.status_code)
        assert Question.objects.filter(title='A test question')

    @mock.patch.object(Site.objects, 'get_current')
    def test_aaq_new_question_inactive(self, get_current):
        """New question is posted through mobile."""
        get_current.return_value.domain = 'testserver'

        # Log in first.
        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

        # Then become inactive.
        u.is_active = False
        u.save()

        # Set 'in-aaq' for the session. It isn't already set because this
        # test doesn't do a GET of the form first.
        s = self.client.session
        s['in-aaq'] = True
        s.save()

        response = self._new_question(post_it=True)
        eq_(200, response.status_code)
        assert template_used(response, 'questions/mobile/confirm_email.html')

    def test_aaq_login_form(self):
        """The AAQ authentication forms contain the identifying fields.

        Added this test because it is hard to debug what happened when this
        fields somehow go missing.
        """
        res = self._new_question()
        doc = pq(res.content)
        eq_(1, len(doc('#login-form input[name=login]')))
        eq_(1, len(doc('#register-form input[name=register]')))


@set_waffle_flag('new_aaq')
class ReactAAQTests(TestCaseBase):

    def test_waffle_flag(self):
        url = reverse('questions.aaq_step1')
        response = self.client.get(url, follow=True)
        assert template_used(response, 'questions/new_question_react.html')

    def test_only_marked_topics(self):
        t1 = TopicFactory(in_aaq=True)
        TopicFactory(in_aaq=False)

        url = reverse('questions.aaq_step1')
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        topics = json.loads(doc('.data[name=topics]').text())

        eq_(len(topics), 1)
        eq_(topics[0]['id'], t1.id)


class TestQuestionUpdates(TestCaseBase):
    """Tests that questions are only updated in the right cases."""
    client_class = LocalizingClient

    date_format = '%Y%M%d%H%m%S'

    def setUp(self):
        super(TestQuestionUpdates, self).setUp()
        self.u = UserFactory(is_superuser=True)
        self.client.login(username=self.u.username, password='testpass')

        self.q = QuestionFactory(updated=datetime(2012, 7, 9, 9, 0, 0))
        self.a = AnswerFactory(question=self.q)

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


class TroubleshootingParsingTests(TestCaseBase):

    def test_empty_troubleshooting_info(self):
        """Test a troubleshooting value that is valid JSON, but junk.
        This should trigger the parser to return None, which should not
        cause a 500.
        """
        q = QuestionFactory()
        q.add_metadata(troubleshooting='{"foo": "bar"}')

        # This case should not raise an error.
        response = get(self.client, 'questions.details', args=[q.id])
        eq_(200, response.status_code)

    def test_weird_list_troubleshooting_info(self):
        """Test the corner case in which 'modifiedPReferences' is in a
        list in troubleshooting data. This is weird, but caused a bug."""
        q = QuestionFactory()
        q.add_metadata(troubleshooting='["modifiedPreferences"]')

        # This case should not raise an error.
        response = get(self.client, 'questions.details', args=[q.id])
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


class TestQuestionList(TestCaseBase):
    def test_locale_filter(self):
        """Only questions for the current locale should be shown on the
        questions front page for AAQ locales."""

        eq_(Question.objects.count(), 0)
        p = ProductFactory(slug=u'firefox')
        TopicFactory(title='Fix problems', slug='fix-problems', product=p)

        QuestionFactory(title='question cupcakes?', product=p, locale='en-US')
        QuestionFactory(title='question donuts?', product=p, locale='en-US')
        QuestionFactory(title='question pies?', product=p, locale='pt-BR')
        QuestionFactory(title='question pastries?', product=p, locale='de')

        def sub_test(locale, *titles):
            url = urlparams(reverse(
                'questions.list', args=['all'], locale=locale))
            response = self.client.get(url, follow=True)
            doc = pq(response.content)
            eq_msg(len(doc('section[id^=question]')), len(titles),
                   'Wrong number of results for {0}'.format(locale))
            for substr in titles:
                assert substr in doc('.questions section .content h2 a').text()

        # en-US and pt-BR are both in AAQ_LANGUAGES, so should be filtered.
        sub_test('en-US', 'cupcakes?', 'donuts?')
        sub_test('pt-BR', 'pies?')
        # de is not in AAQ_LANGUAGES, so should show en-US, but not pt-BR
        sub_test('de', 'cupcakes?', 'donuts?', 'pastries?')


class TestQuestionReply(TestCaseBase):
    def setUp(self):
        u = UserFactory()
        self.client.login(username=u.username, password='testpass')
        self.question = QuestionFactory()

    def test_reply_to_spam_question(self):
        self.question.is_spam = True
        self.question.save()

        res = self.client.post(
            reverse('questions.reply', args=[self.question.id]),
            {'content': 'The best reply evar!'})
        eq_(res.status_code, 404)

    def test_needs_info(self):
        eq_(self.question.needs_info, False)

        res = self.client.post(
            reverse('questions.reply', args=[self.question.id]),
            {'content': 'More info please', 'needsinfo': ''})
        eq_(res.status_code, 302)

        q = Question.objects.get(id=self.question.id)
        eq_(q.needs_info, True)

    def test_clear_needs_info(self):
        self.question.set_needs_info()
        eq_(self.question.needs_info, True)

        res = self.client.post(
            reverse('questions.reply', args=[self.question.id]),
            {'content': 'More info please', 'clear_needsinfo': ''})
        eq_(res.status_code, 302)

        q = Question.objects.get(id=self.question.id)
        eq_(q.needs_info, False)


class TestMarkingSolved(TestCaseBase):
    def setUp(self):
        u = UserFactory()
        self.client.login(username=u.username, password='testpass')
        self.question = QuestionFactory(creator=u)
        self.answer = AnswerFactory(question=self.question)

    def test_cannot_mark_spam_answer(self):
        self.answer.is_spam = True
        self.answer.save()

        res = self.client.get(
            reverse('questions.solve',
                    args=[self.question.id, self.answer.id]))
        eq_(res.status_code, 404)

    def test_cannot_mark_answers_on_spam_question(self):
        self.question.is_spam = True
        self.question.save()

        res = self.client.get(
            reverse('questions.solve',
                    args=[self.question.id, self.answer.id]))
        eq_(res.status_code, 404)


class TestVoteAnswers(TestCaseBase):
    def setUp(self):
        u = UserFactory()
        self.client.login(username=u.username, password='testpass')
        self.question = QuestionFactory()
        self.answer = AnswerFactory(question=self.question)

    def test_cannot_vote_for_answers_on_spam_question(self):
        self.question.is_spam = True
        self.question.save()

        res = self.client.post(
            reverse('questions.answer_vote',
                    args=[self.question.id, self.answer.id]))
        eq_(res.status_code, 404)

    def test_cannot_vote_for_answers_marked_spam(self):
        self.answer.is_spam = True
        self.answer.save()

        res = self.client.post(
            reverse('questions.answer_vote',
                    args=[self.question.id, self.answer.id]))
        eq_(res.status_code, 404)


class TestVoteQuestions(TestCaseBase):
    def setUp(self):
        u = UserFactory()
        self.client.login(username=u.username, password='testpass')
        self.question = QuestionFactory()

    def test_cannot_vote_on_spam_question(self):
        self.question.is_spam = True
        self.question.save()

        res = self.client.post(
            reverse('questions.vote', args=[self.question.id]))
        eq_(res.status_code, 404)


class TestQuestionDetails(TestCaseBase):
    def setUp(self):
        self.question = QuestionFactory()

    def test_mods_can_see_spam_details(self):
        self.question.is_spam = True
        self.question.save()

        res = get(self.client, 'questions.details', args=[self.question.id])
        eq_(404, res.status_code)

        u = UserFactory()
        add_permission(u, FlaggedObject, 'can_moderate')
        self.client.login(username=u.username, password='testpass')

        res = get(self.client, 'questions.details', args=[self.question.id])
        eq_(200, res.status_code)


class TestRateLimiting(TestCaseBase):
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
        questions = [QuestionFactory() for _ in range(11)]

        # The rate limit is 10 per day. So make 10 requests. (0 through 9)
        for i in range(10):
            self._check_question_vote(questions[i], False)

        # Now make another, it should fail.
        self._check_question_vote(questions[10], True)

    def test_answer_vote_limit(self):
        """Test that an anonymous user's votes are ignored after 10
        answer votes."""
        q = QuestionFactory()
        answers = AnswerFactory.create_batch(11, question=q)

        # The rate limit is 10 per day. So make 10 requests. (0 through 9)
        for i in range(10):
            self._check_answer_vote(q, answers[i], False)

        # Now make another, it should fail.
        self._check_answer_vote(q, answers[10], True)

    def test_question_vote_logged_in(self):
        """This exhausts the rate limit, then logs in, and exhausts it
        again."""
        questions = [QuestionFactory() for _ in range(11)]
        u = UserFactory(password='testpass')

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
        q = QuestionFactory()
        answers = [AnswerFactory(question=q) for _ in range(12)]
        u = UserFactory(password='testpass')

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
        u = UserFactory(password='testpass')
        self.client.login(username=u.username, password='testpass')

        q = QuestionFactory()
        content = 'lorem ipsum dolor sit amet'
        url = reverse('questions.reply', args=[q.id])
        for i in range(7):
            self.client.post(url, {'content': content})

        eq_(4, Answer.objects.count())


class TestScreenShare(TestCaseBase):
    def setUp(self):
        self.user = UserFactory()
        add_permission(self.user, Profile, 'screen_share')
        self.question = QuestionFactory()

    def test_screen_share_answer(self):
        """Test that the answer gets created when the screen sharing invite is sent."""
        eq_(self.question.answers.count(), 0)
        self.client.login(username=self.user.username, password='testpass')
        url = reverse('questions.screen_share', args=[self.question.id])
        res = self.client.post(url, follow=True)
        eq_(res.status_code, 200)
        eq_(self.question.answers.count(), 1)

    def test_screen_share_metadata(self):
        """Test that the screen sharing meta data is added to the question."""
        eq_(self.question.metadata.get('screen_sharing'), None)
        self.client.login(username=self.user.username, password='testpass')
        url = reverse('questions.screen_share', args=[self.question.id])
        res = self.client.post(url, follow=True)
        eq_(res.status_code, 200)
        q = Question.objects.get(pk=self.question.pk)
        eq_(q.metadata.get('screen_sharing'), 'true')


class TestStats(ElasticTestCase):
    client_class = LocalizingClient

    def test_stats(self):
        """Tests questions/dashboard/metrics view"""
        p = ProductFactory()
        t = TopicFactory(title='Websites', slug='websites', product=p)

        QuestionFactory(
            title=u'cupcakes',
            content=u'Cupcakes rock!',
            created=datetime.now() - timedelta(days=1),
            topic=t)

        self.refresh()

        response = self.client.get(reverse('questions.metrics'))
        eq_(200, response.status_code)

        # If there's histogram data, this is probably good enough to
        # denote its existence.
        assert ' data-graph="[' in response.content


class TestEditDetails(TestCaseBase):
    def setUp(self):
        u = UserFactory()
        add_permission(u, Question, 'change_question')
        assert u.has_perm('questions.change_question')
        self.user = u

        p = ProductFactory()
        t = TopicFactory(product=p)

        q = QuestionFactory(product=p, topic=t)

        self.product = p
        self.topic = t
        self.question = q

    def _request(self, user=None, data=None):
        """Make a request to edit details"""
        if user is None:
            user = self.user
        self.client.login(username=user.username, password='testpass')
        url = reverse('questions.edit_details',
                      kwargs={'question_id': self.question.id})
        return self.client.post(url, data=data)

    def test_permissions(self):
        """Test that the new permission works"""
        data = {
            'product': self.product.id,
            'topic': self.topic.id,
            'locale': self.question.locale
        }

        u = UserFactory()
        response = self._request(u, data=data)
        eq_(403, response.status_code)

        response = self._request(data=data)
        eq_(302, response.status_code)

    def test_missing_data(self):
        """Test for missing data"""
        data = {
            'product': self.product.id,
            'locale': self.question.locale
        }
        response = self._request(data=data)
        eq_(400, response.status_code)

        data = {
            'topic': self.topic.id,
            'locale': self.question.locale
        }
        response = self._request(data=data)
        eq_(400, response.status_code)

        data = {
            'product': self.product.id,
            'topic': self.topic.id
        }
        response = self._request(data=data)
        eq_(400, response.status_code)

    def test_bad_data(self):
        """Test for bad data"""
        data = {
            'product': ProductFactory().id,
            'topic': TopicFactory().id,
            'locale': self.question.locale
        }
        response = self._request(data=data)
        eq_(400, response.status_code)

        data = {
            'product': self.product.id,
            'topic': self.topic.id,
            'locale': 'zu'
        }
        response = self._request(data=data)
        eq_(400, response.status_code)

    def test_change_topic(self):
        """Test changing the topic"""
        t_new = TopicFactory(product=self.product)

        data = {
            'product': self.product.id,
            'topic': t_new.id,
            'locale': self.question.locale
        }

        assert t_new.id != self.topic.id

        response = self._request(data=data)
        eq_(302, response.status_code)

        q = Question.objects.get(id=self.question.id)

        eq_(t_new.id, q.topic.id)

    def test_change_product(self):
        """Test changing the product"""
        t_new = TopicFactory()
        p_new = t_new.product

        assert self.topic.id != t_new.id
        assert self.product.id != p_new.id

        data = {
            'product': p_new.id,
            'topic': t_new.id,
            'locale': self.question.locale
        }

        response = self._request(data=data)
        eq_(302, response.status_code)

        q = Question.objects.get(id=self.question.id)
        eq_(p_new.id, q.product.id)
        eq_(t_new.id, q.topic.id)

    def test_change_locale(self):
        locale = 'hu'

        assert locale in QuestionLocale.objects.locales_list()
        assert locale != self.question.locale

        data = {
            'product': self.product.id,
            'topic': self.topic.id,
            'locale': locale
        }

        response = self._request(data=data)
        eq_(302, response.status_code)

        q = Question.objects.get(id=self.question.id)
        eq_(q.locale, locale)
