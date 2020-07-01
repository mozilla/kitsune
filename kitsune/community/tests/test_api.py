from datetime import datetime
from datetime import timedelta

from django.test.client import RequestFactory
from nose.tools import eq_

from kitsune.community import api
from kitsune.products.tests import ProductFactory
from kitsune.questions.tests import AnswerFactory
from kitsune.questions.tests import AnswerVoteFactory
from kitsune.search.tests import ElasticTestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import RevisionFactory


class TestTopContributorsBase(ElasticTestCase):
    """Tests for the Community Hub top users API."""

    def setUp(self):
        super(TestTopContributorsBase, self).setUp()
        self.factory = RequestFactory()
        self.api = api.TopContributorsBase()
        self.api.get_data = lambda request: {}

    def test_invalid_filter_name(self):
        req = self.factory.get('/', {'not_valid': 'wrong'})
        self.api.request = req
        self.api.get_filters()
        eq_(self.api.warnings, ['Unknown filter not_valid'])


class TestTopContributorsQuestions(ElasticTestCase):
    def setUp(self):
        super(TestTopContributorsQuestions, self).setUp()
        self.factory = RequestFactory()
        self.api = api.TopContributorsQuestions()

    def test_it_works(self):
        u1 = UserFactory()
        u2 = UserFactory()

        a1 = AnswerFactory(creator=u1)
        a2 = AnswerFactory(creator=u1)
        a3 = AnswerFactory(creator=u2)

        a1.question.solution = a1
        a1.question.save()
        AnswerVoteFactory(answer=a3, helpful=True)

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

    def test_filter_by_product(self):
        u1 = UserFactory()
        u2 = UserFactory()

        p1 = ProductFactory()
        p2 = ProductFactory()

        AnswerFactory(question__product=p1, creator=u1)
        AnswerFactory(question__product=p2, creator=u1)
        AnswerFactory(question__product=p2, creator=u2)

        self.refresh()

        req = self.factory.get('/', {'product': p1.slug})
        data = self.api.get_data(req)

        eq_(data['count'], 1)
        eq_(data['results'][0]['user']['username'], u1.username)
        eq_(data['results'][0]['answer_count'], 1)

    def test_page_size(self):
        u1 = UserFactory()
        u2 = UserFactory()

        AnswerFactory(creator=u1)
        AnswerFactory(creator=u2)

        self.refresh()

        req = self.factory.get('/', {'page_size': 2})
        data = self.api.get_data(req)
        eq_(data['count'], 2)
        eq_(len(data['results']), 2)

        req = self.factory.get('/', {'page_size': 1})
        data = self.api.get_data(req)
        eq_(data['count'], 2)
        eq_(len(data['results']), 1)

    def test_filter_last_contribution(self):
        u1 = UserFactory()
        u2 = UserFactory()

        today = datetime.now()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = yesterday - timedelta(days=1)

        AnswerFactory(creator=u1, created=today)
        AnswerFactory(creator=u1, created=day_before_yesterday)
        AnswerFactory(creator=u2, created=day_before_yesterday)

        self.refresh()

        # Test 1

        req = self.factory.get('/', {'last_contribution_date__gt': yesterday.strftime('%Y-%m-%d')})
        data = self.api.get_data(req)

        eq_(data['count'], 1)
        eq_(data['results'][0]['user']['username'], u1.username)
        # Even though only 1 contribution was made in the time range, this filter
        # is only checking the last contribution time, so both are included.
        eq_(data['results'][0]['answer_count'], 2)

        # Test 2

        req = self.factory.get('/', {'last_contribution_date__lt': yesterday.strftime('%Y-%m-%d')})
        data = self.api.get_data(req)

        eq_(data['count'], 1)
        eq_(data['results'][0]['user']['username'], u2.username)
        eq_(data['results'][0]['answer_count'], 1)


class TestTopContributorsLocalization(ElasticTestCase):
    def setUp(self):
        super(TestTopContributorsLocalization, self).setUp()
        self.factory = RequestFactory()
        self.api = api.TopContributorsLocalization()

    def test_it_works(self):
        u1 = UserFactory()
        u2 = UserFactory()

        RevisionFactory(creator=u1)
        r2 = RevisionFactory(creator=u1, reviewer=u2)
        r3 = RevisionFactory(creator=u2)

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

    def test_filter_by_product(self):
        u1 = UserFactory()
        u2 = UserFactory()

        p1 = ProductFactory()
        p2 = ProductFactory()

        RevisionFactory(document__products=[p1], creator=u1)
        RevisionFactory(document__products=[p2], creator=u1)
        RevisionFactory(document__products=[p2], creator=u2)

        self.refresh()

        req = self.factory.get('/', {'product': p1.slug})
        data = self.api.get_data(req)

        eq_(data['count'], 1)
        eq_(data['results'][0]['user']['username'], u1.username)
        eq_(data['results'][0]['revision_count'], 1)

    def test_page_size(self):
        u1 = UserFactory()
        u2 = UserFactory()

        RevisionFactory(creator=u1)
        RevisionFactory(creator=u2)

        self.refresh()

        req = self.factory.get('/', {'page_size': 2})
        data = self.api.get_data(req)
        eq_(data['count'], 2)
        eq_(len(data['results']), 2)

        req = self.factory.get('/', {'page_size': 1})
        data = self.api.get_data(req)
        eq_(data['count'], 2)
        eq_(len(data['results']), 1)

    def test_filter_last_contribution(self):
        u1 = UserFactory()
        u2 = UserFactory()

        today = datetime.now()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = yesterday - timedelta(days=1)

        RevisionFactory(creator=u1, created=today)
        RevisionFactory(creator=u1, created=day_before_yesterday)
        RevisionFactory(creator=u2, created=day_before_yesterday)

        self.refresh()

        # Test 1

        req = self.factory.get('/', {'last_contribution_date__gt': yesterday.strftime('%Y-%m-%d')})
        data = self.api.get_data(req)

        eq_(data['count'], 1)
        eq_(data['results'][0]['user']['username'], u1.username)
        # Even though only 1 contribution was made in the time range, this filter
        # is only checking the last contribution time, so both are included.
        eq_(data['results'][0]['revision_count'], 2)

        # Test 2

        req = self.factory.get('/', {'last_contribution_date__lt': yesterday.strftime('%Y-%m-%d')})
        data = self.api.get_data(req)

        eq_(data['count'], 1)
        eq_(data['results'][0]['user']['username'], u2.username)
        eq_(data['results'][0]['revision_count'], 1)
