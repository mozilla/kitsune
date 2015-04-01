from nose.tools import eq_, raises

from django.test.client import RequestFactory

from kitsune.community import api
from kitsune.questions.tests import answer, answervote
from kitsune.search.tests import ElasticTestCase
from kitsune.users.tests import profile
from kitsune.wiki.tests import revision


class TestTopContributorsBase(ElasticTestCase):
    """Tests for the Community Hub top users API."""

    def setUp(self):
        super(TestTopContributorsBase, self).setUp()
        self.factory = RequestFactory()
        self.api = api.TopContributorsBase()
        self.api.get_data = lambda request: {}

    @raises(api.InvalidFilterNameException)
    def test_test_invalid_filter_name(self):
        req = self.factory.get('/', {'not_valid': 'wrong'})
        self.api.request = req
        self.api.get_filters()


class TestTopContributorsQuestions(ElasticTestCase):
    def setUp(self):
        super(TestTopContributorsQuestions, self).setUp()
        self.factory = RequestFactory()
        self.api = api.TopContributorsQuestions()

    def test_it_works(self):
        u1 = profile().user
        u2 = profile().user

        a1 = answer(creator=u1, save=True)  # noqa
        a2 = answer(creator=u1, save=True)
        a3 = answer(creator=u2, save=True)

        a1.question.solution = a1
        a1.question.save()
        answervote(answer=a3, helpful=True, save=True)

        self.refresh()

        req = self.factory.get('/')
        data = self.api.get_data(req)

        eq_(data['count'], 2)

        eq_(data['results'][0]['user']['username'], u1.username)
        eq_(data['results'][0]['rank'], 1)
        eq_(data['results'][0]['answer_count'], 2)
        eq_(data['results'][0]['solution_count'], 1)
        eq_(data['results'][0]['helpful_vote_count'], 0)
        eq_(data['results'][0]['last_contribution_date'], a2.created.replace(microsecond=0))

        eq_(data['results'][1]['user']['username'], u2.username)
        eq_(data['results'][1]['rank'], 2)
        eq_(data['results'][1]['answer_count'], 1)
        eq_(data['results'][1]['solution_count'], 0)
        eq_(data['results'][1]['helpful_vote_count'], 1)
        eq_(data['results'][1]['last_contribution_date'], a3.created.replace(microsecond=0))


class TestTopContributorsLocalization(ElasticTestCase):
    def setUp(self):
        super(TestTopContributorsLocalization, self).setUp()
        self.factory = RequestFactory()
        self.api = api.TopContributorsLocalization()

    def test_it_works(self):
        u1 = profile().user
        u2 = profile().user

        r1 = revision(creator=u1, save=True)  # noqa
        r2 = revision(creator=u1, save=True)
        r3 = revision(creator=u2, save=True)

        r2.reviewer = u2
        r2.save()

        self.refresh()

        req = self.factory.get('/')
        data = self.api.get_data(req)

        eq_(data['count'], 2)

        eq_(data['results'][0]['user']['username'], u1.username)
        eq_(data['results'][0]['rank'], 1)
        eq_(data['results'][0]['revision_count'], 2)
        eq_(data['results'][0]['review_count'], 0)
        eq_(data['results'][0]['last_contribution_date'], r2.created.replace(microsecond=0))

        eq_(data['results'][1]['user']['username'], u2.username)
        eq_(data['results'][1]['rank'], 2)
        eq_(data['results'][1]['revision_count'], 1)
        eq_(data['results'][1]['review_count'], 1)
        eq_(data['results'][1]['last_contribution_date'], r3.created.replace(microsecond=0))
