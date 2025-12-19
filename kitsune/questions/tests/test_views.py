import json
from datetime import datetime

from django.conf import settings
from django.test.utils import override_settings
from pyquery import PyQuery as pq

from kitsune.flagit.models import FlaggedObject
from kitsune.products.models import ProductSupportConfig
from kitsune.products.tests import ProductFactory, ProductSupportConfigFactory, TopicFactory
from kitsune.questions.models import (
    AAQConfig,
    Answer,
    AnswerVote,
    Question,
    QuestionLocale,
    QuestionVote,
)
from kitsune.questions.tests import (
    AAQConfigFactory,
    AnswerFactory,
    QuestionFactory,
    QuestionLocaleFactory,
)
from kitsune.questions.views import parse_troubleshooting
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase, eq_msg, get, template_used
from kitsune.sumo.urlresolvers import reverse
from kitsune.tidings.models import Watch
from kitsune.users.tests import UserFactory, add_permission


class AAQSearchTests(ElasticTestCase):
    search_tests = True

    def test_ratelimit(self):
        """Make sure posting new questions is ratelimited"""
        p = ProductFactory(slug="firefox")
        locale, _ = QuestionLocale.objects.get_or_create(locale=settings.LANGUAGE_CODE)
        aaq_config = AAQConfigFactory(product=p, enabled_locales=[locale], is_active=True)
        ProductSupportConfigFactory(
            product=p,
            forum_config=aaq_config,
            is_active=True,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM
        )
        topic = TopicFactory(slug="troubleshooting", products=[p], in_aaq=True)
        data = {
            "title": "A test question",
            "content": "I have this question that I hope...",
            "category": topic.id,
            "ff_version": "3.6.6",
            "os": "Intel Mac OS X 10.6",
            "plugins": "* Shockwave Flash 10.1 r53",
            "useragent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X "
            "10.6; en-US; rv:1.9.2.6) Gecko/20100625 "
            "Firefox/3.6.6",
        }
        url = urlparams(
            reverse("questions.aaq_step3", args=["firefox"]),
            search="A test question",
        )

        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        for i in range(0, 5):
            self.client.post(url, data, follow=True)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(403, response.status_code)

    def test_first_step(self):
        """Make sure the first step doesn't blow up

        Oddly, none of the other tests cover this simple case.
        """
        url = reverse("questions.aaq_step1")
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)

    @override_settings(WIKI_DEFAULT_LANGUAGE="fr")
    def test_no_redirect_english(self):
        """The default language should never redirect, even if it isn't an AAQ language."""
        """Non-AAQ locales should redirect."""
        url_fr = reverse("questions.aaq_step1", locale="fr")
        res = self.client.get(url_fr)
        self.assertEqual(200, res.status_code)


class AAQTests(TestCase):
    def setUp(self):
        product = ProductFactory(title="Firefox", slug="firefox")
        locale, _ = QuestionLocale.objects.get_or_create(locale=settings.LANGUAGE_CODE)
        aaq_config = AAQConfigFactory(product=product, enabled_locales=[locale], is_active=True)
        # Create ProductSupportConfig for routing
        ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            is_active=True,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM
        )

    def test_non_authenticated_user(self):
        """
        A non-authenticated user cannot access the create question stage of the
        AAQ flow and will be redirected to auth screen
        """
        url = reverse("questions.aaq_step3", args=["desktop"])
        response = self.client.get(url, follow=True)
        assert template_used(response, "users/auth.html")

    def test_inactive_user(self):
        """
        An inactive user cannot access the create question stage of the AAQ flow
        """
        user = UserFactory(is_superuser=False)
        self.client.login(username=user.username, password="testpass")

        # After log in, set user to inactive
        user.is_active = False
        user.save()

        url = reverse("questions.aaq_step3", args=["desktop"])
        response = self.client.get(url, follow=True)
        assert not template_used(response, "questions/new_question.html")

    def test_authenticated_user(self):
        """
        An active, authenticated user can access the create question stage of the AAQ flow
        """
        user = UserFactory(is_superuser=False)
        self.client.login(username=user.username, password="testpass")
        url = reverse("questions.aaq_step3", args=["firefox"])
        response = self.client.get(url, follow=True)
        assert not template_used(response, "users/auth.html")
        assert template_used(response, "questions/new_question.html")


class TestQuestionUpdates(TestCase):
    """Tests that questions are only updated in the right cases."""

    date_format = "%Y%M%d%H%m%S"

    def setUp(self):
        super().setUp()
        self.u = UserFactory(is_superuser=True)
        self.client.login(username=self.u.username, password="testpass")

        self.q = QuestionFactory(updated=datetime(2012, 7, 9, 9, 0, 0))
        self.a = AnswerFactory(question=self.q)

        # Get the question from the database so we have a consistent level of
        # precision during the test.
        self.q = Question.objects.get(pk=self.q.id)

    def tearDown(self):
        self.client.logout()
        self.u.delete()
        self.q.delete()

    def _request_and_no_update(self, url, req_type="POST", data=None):
        if data is None:
            data = {}
        updated = self.q.updated

        if req_type == "POST":
            self.client.post(url, data, follow=True)
        elif req_type == "GET":
            self.client.get(url, data, follow=True)
        else:
            raise ValueError('req_type must be either "GET" or "POST"')

        self.q = Question.objects.get(pk=self.q.id)
        self.assertEqual(
            updated.strftime(self.date_format),
            self.q.updated.strftime(self.date_format),
        )

    def test_no_update_solve(self):
        url = urlparams(reverse("questions.solve", args=[self.q.id, self.a.id]))
        self._request_and_no_update(url)

    def test_no_update_unsolve(self):
        url = urlparams(reverse("questions.unsolve", args=[self.q.id, self.a.id]))
        self._request_and_no_update(url)

    def test_no_update_vote(self):
        url = urlparams(reverse("questions.vote", args=[self.q.id]))
        self._request_and_no_update(url, req_type="POST")

    def test_no_update_lock(self):
        url = urlparams(reverse("questions.lock", args=[self.q.id]))
        self._request_and_no_update(url, req_type="POST")
        # Now unlock
        self._request_and_no_update(url, req_type="POST")

    def test_no_update_tagging(self):
        url = urlparams(reverse("questions.add_tag", args=[self.q.id]))
        self._request_and_no_update(url, req_type="POST", data={"tag-name": "foo"})

        url = urlparams(reverse("questions.remove_tag", args=[self.q.id]))
        self._request_and_no_update(url, req_type="POST", data={"remove-tag-foo": 1})


class TroubleshootingParsingTests(TestCase):
    def test_empty_troubleshooting_info(self):
        """Test a troubleshooting value that is valid JSON, but junk.
        This should trigger the parser to return None, which should not
        cause a 500.
        """
        q = QuestionFactory()
        q.add_metadata(troubleshooting='{"foo": "bar"}')

        # This case should not raise an error.
        response = get(self.client, "questions.details", args=[q.id])
        self.assertEqual(200, response.status_code)

    def test_weird_list_troubleshooting_info(self):
        """Test the corner case in which 'modifiedPReferences' is in a
        list in troubleshooting data. This is weird, but caused a bug."""
        q = QuestionFactory()
        q.add_metadata(troubleshooting='["modifiedPreferences"]')

        # This case should not raise an error.
        response = get(self.client, "questions.details", args=[q.id])
        self.assertEqual(200, response.status_code)

    def test_string_keys_troubleshooting(self):
        """Test something that looks like troubleshooting data, but
        isn't formatted quite right. The parser should return None to
        indicate that something isn't right."""
        troubleshooting = """{
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
        }"""

        assert parse_troubleshooting(troubleshooting) is None

    def test_troubleshooting_parser(self):
        """Test that the troubleshooting parser likes good data."""
        troubleshooting = """
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
            }"""

        assert parse_troubleshooting(troubleshooting) is not None


class TestQuestionList(TestCase):
    def test_locale_filter(self):
        """Only questions for the current locale should be shown on the
        questions front page for AAQ locales."""

        for locale in (settings.LANGUAGE_CODE, "pt-BR"):
            QuestionLocale.objects.get_or_create(locale=locale)
        self.assertEqual(Question.objects.count(), 0)
        p = ProductFactory(slug="firefox")
        TopicFactory(title="Fix problems", slug="fix-problems", products=[p])
        AAQConfigFactory(product=p, is_active=True, enabled_locales=QuestionLocale.objects.all())

        QuestionFactory(title="question cupcakes?", product=p, locale="en-US")
        QuestionFactory(title="question donuts?", product=p, locale="en-US")
        QuestionFactory(title="question pies?", product=p, locale="pt-BR")
        QuestionFactory(title="question pastries?", product=p, locale="de")

        def sub_test(locale, *titles):
            url = urlparams(reverse("questions.list", args=["all"], locale=locale))
            response = self.client.get(url, follow=True)
            doc = pq(response.content)
            eq_msg(
                len(doc("article[id^=question]")),
                len(titles),
                "Wrong number of results for {}".format(locale),
            )
            for substr in titles:
                assert substr in doc(".forum--question-item-heading a").text()

        # en-US and pt-BR are both in AAQ_LANGUAGES, so should be filtered.
        sub_test("en-US", "cupcakes?", "donuts?")
        sub_test("pt-BR", "pies?")
        # de is not in AAQ_LANGUAGES, so should show en-US, but not pt-BR
        sub_test("de", "cupcakes?", "donuts?", "pastries?")


class TestQuestionReply(TestCase):
    def setUp(self):
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        self.question = QuestionFactory()

    def test_reply_to_spam_question(self):
        self.question.is_spam = True
        self.question.save()

        res = self.client.post(
            reverse("questions.reply", args=[self.question.id]),
            {"content": "The best reply evar!"},
        )
        self.assertEqual(res.status_code, 404)

    def test_needs_info(self):
        self.assertEqual(self.question.needs_info, False)

        res = self.client.post(
            reverse("questions.reply", args=[self.question.id]),
            {"content": "More info please", "needsinfo": ""},
        )
        self.assertEqual(res.status_code, 302)

        q = Question.objects.get(id=self.question.id)
        self.assertEqual(q.needs_info, True)

    def test_clear_needs_info(self):
        self.question.set_needs_info()
        self.assertEqual(self.question.needs_info, True)

        res = self.client.post(
            reverse("questions.reply", args=[self.question.id]),
            {"content": "More info please", "clear_needsinfo": ""},
        )
        self.assertEqual(res.status_code, 302)

        q = Question.objects.get(id=self.question.id)
        self.assertEqual(q.needs_info, False)


class TestMarkingSolved(TestCase):
    def setUp(self):
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        self.question = QuestionFactory(creator=u)
        self.answer = AnswerFactory(question=self.question)

    def test_cannot_mark_spam_answer(self):
        self.answer.is_spam = True
        self.answer.save()

        res = self.client.post(reverse("questions.solve", args=[self.question.id, self.answer.id]))
        self.assertEqual(res.status_code, 404)

    def test_cannot_mark_answers_on_spam_question(self):
        self.question.is_spam = True
        self.question.save()

        res = self.client.post(reverse("questions.solve", args=[self.question.id, self.answer.id]))
        self.assertEqual(res.status_code, 404)

    def test_mark_as_solved_via_watch_secret(self):
        self.client.logout()

        watch = Watch.objects.create(
            secret="abcdefghjk", event_type="question reply", user=self.question.creator
        )

        url = urlparams(
            reverse("questions.solve", args=[self.question.id, self.answer.id]),
            watch=watch.secret,
        )

        self.assertIsNone(self.question.solution)

        res = self.client.get(url)

        self.assertEqual(res.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.solution, self.answer)
        # Ensure that the secret has been changed.
        watch.refresh_from_db()
        self.assertNotEqual(watch.secret, "abcdefghjk")

    def test_mark_as_solved_with_invalid_watch_secret(self):
        self.client.logout()

        watch = Watch.objects.create(
            secret="abcdefghjk", event_type="question reply", user=self.question.creator
        )

        url = urlparams(
            reverse("questions.solve", args=[self.question.id, self.answer.id]),
            watch="PQRTUVWXYZ",
        )

        self.assertIsNone(self.question.solution)

        res = self.client.get(url)

        self.assertEqual(res.status_code, 403)
        # Ensure that the question hasn't been solved and the watch secret hasn't changed.
        self.question.refresh_from_db()
        self.assertIsNone(self.question.solution)
        watch.refresh_from_db()
        self.assertEqual(watch.secret, "abcdefghjk")

    def test_mark_as_solved_with_no_watch_secret(self):
        self.client.logout()

        url = reverse("questions.solve", args=[self.question.id, self.answer.id])

        self.assertIsNone(self.question.solution)

        res = self.client.get(url)

        self.assertEqual(res.status_code, 403)
        self.question.refresh_from_db()
        self.assertIsNone(self.question.solution)


class TestVoteAnswers(TestCase):
    def setUp(self):
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        self.question = QuestionFactory()
        self.answer = AnswerFactory(question=self.question)

    def test_cannot_vote_for_answers_on_spam_question(self):
        self.question.is_spam = True
        self.question.save()

        res = self.client.post(
            reverse("questions.answer_vote", args=[self.question.id, self.answer.id])
        )
        self.assertEqual(res.status_code, 404)

    def test_cannot_vote_for_answers_marked_spam(self):
        self.answer.is_spam = True
        self.answer.save()

        res = self.client.post(
            reverse("questions.answer_vote", args=[self.question.id, self.answer.id])
        )
        self.assertEqual(res.status_code, 404)

    def test_anonymous_user_cannot_vote_on_answer(self):
        """Anonymous users cannot vote on answers and are redirected to login."""
        self.client.logout()

        res = self.client.post(
            reverse("questions.answer_vote", args=[self.question.id, self.answer.id]),
            {"helpful": "y"},
        )

        # Should redirect to login page
        self.assertEqual(res.status_code, 302)
        self.assertIn(settings.LOGIN_URL, res.url)

    def test_authenticated_user_can_vote_on_answer(self):
        """Authenticated users can vote on answers."""
        res = self.client.post(
            reverse("questions.answer_vote", args=[self.question.id, self.answer.id]),
            {"helpful": "y"},
        )

        # Should redirect to answer (successful vote)
        self.assertEqual(res.status_code, 302)

        # Verify vote was created
        self.assertEqual(AnswerVote.objects.filter(answer=self.answer).count(), 1)
        vote = AnswerVote.objects.get(answer=self.answer)
        self.assertTrue(vote.helpful)


class TestVoteQuestions(TestCase):
    def setUp(self):
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        self.question = QuestionFactory()

    def test_cannot_vote_on_spam_question(self):
        self.question.is_spam = True
        self.question.save()

        res = self.client.post(reverse("questions.vote", args=[self.question.id]))
        self.assertEqual(res.status_code, 404)


class TestQuestionDetails(TestCase):
    def setUp(self):
        self.question = QuestionFactory()

    def test_mods_can_see_spam_details(self):
        self.question.is_spam = True
        self.question.save()

        res = get(self.client, "questions.details", args=[self.question.id])
        self.assertEqual(404, res.status_code)

        u = UserFactory()
        add_permission(u, FlaggedObject, "can_moderate")
        self.client.login(username=u.username, password="testpass")

        res = get(self.client, "questions.details", args=[self.question.id])
        self.assertEqual(200, res.status_code)


class TestRateLimiting(TestCase):
    def _check_question_vote(self, q, ignored):
        """Try and vote on `q`. If `ignored` is false, assert the
        request worked. If `ignored` is True, assert the request didn't
        do anything."""
        url = reverse("questions.vote", args=[q.id], locale="en-US")
        votes = QuestionVote.objects.filter(question=q).count()

        res = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 200)

        data = json.loads(res.content)
        self.assertEqual(data.get("ignored", False), ignored)

        if ignored:
            self.assertEqual(QuestionVote.objects.filter(question=q).count(), votes)
        else:
            self.assertEqual(QuestionVote.objects.filter(question=q).count(), votes + 1)

    def _check_answer_vote(self, q, a, ignored):
        """Try and vote on `a`. If `ignored` is false, assert the
        request worked. If `ignored` is True, assert the request didn't
        do anything."""
        url = reverse("questions.answer_vote", args=[q.id, a.id], locale="en-US")
        votes = AnswerVote.objects.filter(answer=a).count()

        res = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 200)

        data = json.loads(res.content)
        self.assertEqual(data.get("ignored", False), ignored)

        if ignored:
            self.assertEqual(AnswerVote.objects.filter(answer=a).count(), votes)
        else:
            self.assertEqual(AnswerVote.objects.filter(answer=a).count(), votes + 1)

    def test_question_vote_limit(self):
        """Test that an anonymous user's votes are ignored after 1
        question vote."""
        question1 = QuestionFactory()
        question2 = QuestionFactory()

        # The rate limit is 1 per minute. So make 1 request.
        self._check_question_vote(question1, False)

        # Now make another, it should fail.
        self._check_question_vote(question2, True)

    def test_question_vote_logged_in(self):
        """This exhausts the rate limit, then logs in, and exhausts it
        again."""
        question1 = QuestionFactory()
        question2 = QuestionFactory()
        u = UserFactory(password="testpass")

        # The rate limit is 1 per minute. So make 1 request.
        self._check_question_vote(question1, False)

        # Now make another, it should fail.
        self._check_question_vote(question2, True)

        # Login.
        self.client.login(username=u.username, password="testpass")

        # The rate limit is 1 per minute. So make 1 request.
        self._check_question_vote(question1, False)

        # Now make another, it should fail.
        self._check_question_vote(question2, True)

        # Logging out out won't help
        self.client.logout()
        self._check_question_vote(question2, True)

    def test_answer_vote_logged_in(self):
        """Test that different authenticated users have separate rate limits."""
        q = QuestionFactory()
        answer1 = AnswerFactory(question=q)
        answer2 = AnswerFactory(question=q)
        u1 = UserFactory(password="testpass")
        u2 = UserFactory(password="testpass")

        # First user logs in and votes
        self.client.login(username=u1.username, password="testpass")
        # The rate limit is 1 per hour. So make 1 request.
        self._check_answer_vote(q, answer1, False)

        # The rate limit has been hit for this user, so the next request will fail.
        self._check_answer_vote(q, answer2, True)

        # Login as a different user - they should have their own rate limit
        self.client.login(username=u2.username, password="testpass")
        self._check_answer_vote(q, answer1, False)

        # Now the second user has also hit the rate limit.
        self._check_answer_vote(q, answer2, True)

    def test_answers_limit(self):
        """Only four answers per minute can be posted."""
        # Login
        u = UserFactory(password="testpass")
        self.client.login(username=u.username, password="testpass")

        q = QuestionFactory()
        content = "lorem ipsum dolor sit amet"
        url = reverse("questions.reply", args=[q.id])
        for i in range(7):
            self.client.post(url, {"content": content})

        self.assertEqual(4, Answer.objects.count())

    def test_question_watch_limit(self):
        """Test limit of watches on questions per day."""
        q = QuestionFactory()
        url = reverse("questions.watch", args=[q.id], locale="en-US")
        for i in range(15):
            self.client.post(url, {"event_type": "solution", "email": f"ringo{i}@beatles.com"})

        self.assertEqual(Watch.objects.filter(object_id=q.id).count(), 10)


class TestEditDetails(TestCase):
    def setUp(self):
        u = UserFactory()
        add_permission(u, Question, "change_question")
        assert u.has_perm("questions.change_question")
        self.user = u

        AAQConfigFactory(
            enabled_locales=[
                QuestionLocaleFactory(locale=settings.LANGUAGE_CODE),
                QuestionLocaleFactory(locale="hu"),
            ]
        )

        self.product = ProductFactory()
        self.topic = TopicFactory(products=[self.product])
        self.question = QuestionFactory(product=self.product, topic=self.topic)

    def _request(self, user=None, data=None):
        """Make a request to edit details"""
        if user is None:
            user = self.user
        self.client.login(username=user.username, password="testpass")
        url = reverse("questions.edit_details", kwargs={"question_id": self.question.id})
        return self.client.post(url, data=data)

    def test_permissions(self):
        """Test that the new permission works"""
        data = {
            "product": self.product.id,
            "topic": self.topic.id,
            "locale": self.question.locale,
        }

        u = UserFactory()
        response = self._request(u, data=data)
        self.assertEqual(403, response.status_code)

        response = self._request(data=data)
        self.assertEqual(302, response.status_code)

    def test_missing_data(self):
        """Test for missing data"""
        data = {"product": self.product.id, "locale": self.question.locale}
        response = self._request(data=data)
        self.assertEqual(400, response.status_code)

        data = {"topic": self.topic.id, "locale": self.question.locale}
        response = self._request(data=data)
        self.assertEqual(400, response.status_code)

        data = {"product": self.product.id, "topic": self.topic.id}
        response = self._request(data=data)
        self.assertEqual(400, response.status_code)

    def test_bad_data(self):
        """Test for bad data"""
        data = {
            "product": ProductFactory().id,
            "topic": TopicFactory().id,
            "locale": self.question.locale,
        }
        response = self._request(data=data)
        self.assertEqual(400, response.status_code)

        data = {"product": self.product.id, "topic": self.topic.id, "locale": "zu"}
        response = self._request(data=data)
        self.assertEqual(400, response.status_code)

    def test_change_topic(self):
        """Test changing the topic"""
        t_new = TopicFactory(products=[self.product])

        data = {
            "product": self.product.id,
            "topic": t_new.id,
            "locale": self.question.locale,
        }

        assert t_new.id != self.topic.id

        response = self._request(data=data)
        self.assertEqual(302, response.status_code)

        q = Question.objects.get(id=self.question.id)

        self.assertEqual(t_new.id, q.topic.id)

    def test_change_product(self):
        """Test changing the product"""
        t_new = TopicFactory(products=[ProductFactory()])
        p_new = t_new.products.first()

        assert self.topic.id != t_new.id
        assert self.product.id != p_new.id

        data = {"product": p_new.id, "topic": t_new.id, "locale": self.question.locale}

        response = self._request(data=data)
        self.assertEqual(302, response.status_code)

        q = Question.objects.get(id=self.question.id)
        self.assertEqual(p_new.id, q.product.id)
        self.assertEqual(t_new.id, q.topic.id)

    def test_change_locale(self):
        locale = "hu"

        assert locale in AAQConfig.objects.locales_list()
        assert locale != self.question.locale

        data = {"product": self.product.id, "topic": self.topic.id, "locale": locale}

        response = self._request(data=data)
        self.assertEqual(302, response.status_code)

        q = Question.objects.get(id=self.question.id)
        self.assertEqual(q.locale, locale)
