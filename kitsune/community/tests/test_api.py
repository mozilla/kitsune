from datetime import datetime, timedelta

from nose.tools import eq_

from django.test.client import RequestFactory

from kitsune.community import api
from kitsune.products.tests import product
from kitsune.questions.tests import answer, answervote, question
from kitsune.search.tests import ElasticTestCase
from kitsune.users.tests import profile
from kitsune.wiki.tests import document, revision


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

    def test_filter_by_product(self):
        u1 = profile().user
        u2 = profile().user

        p1 = product(save=True)
        p2 = product(save=True)

        q1 = question(product=p1, save=True)
        answer(question=q1, creator=u1, save=True)
        q2 = question(product=p2, save=True)
        answer(question=q2, creator=u1, save=True)
        q3 = question(product=p2, save=True)
        answer(question=q3, creator=u2, save=True)

        self.refresh()

        req = self.factory.get('/', {'product': p1.slug})
        data = self.api.get_data(req)

        eq_(data['count'], 1)
        eq_(data['results'][0]['user']['username'], u1.username)
        eq_(data['results'][0]['answer_count'], 1)

    def test_page_size(self):
        u1 = profile().user
        u2 = profile().user

        q1 = question(save=True)
        answer(question=q1, creator=u1, save=True)
        q2 = question(save=True)
        answer(question=q2, creator=u2, save=True)

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
        u1 = profile().user
        u2 = profile().user

        today = datetime.now()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = yesterday - timedelta(days=1)

        answer(creator=u1, created=today, save=True)
        answer(creator=u1, created=day_before_yesterday, save=True)
        answer(creator=u2, created=day_before_yesterday, save=True)

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

    def test_filter_by_product(self):
        u1 = profile().user
        u2 = profile().user

        p1 = product(save=True)
        p2 = product(save=True)

        d1 = document(save=True)
        d1.products.add(p1)
        revision(document=d1, creator=u1, save=True)

        d2 = document(save=True)
        d2.products.add(p2)
        revision(document=d2, creator=u1, save=True)

        d3 = document(save=True)
        d3.products.add(p2)
        revision(document=d3, creator=u2, save=True)

        self.refresh()

        req = self.factory.get('/', {'product': p1.slug})
        data = self.api.get_data(req)

        eq_(data['count'], 1)
        eq_(data['results'][0]['user']['username'], u1.username)
        eq_(data['results'][0]['revision_count'], 1)

    def test_page_size(self):
        u1 = profile().user
        u2 = profile().user

        d1 = document(save=True)
        revision(document=d1, creator=u1, save=True)

        d2 = document(save=True)
        revision(document=d2, creator=u2, save=True)

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
        u1 = profile().user
        u2 = profile().user

        today = datetime.now()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = yesterday - timedelta(days=1)

        revision(creator=u1, created=today, save=True)
        revision(creator=u1, created=day_before_yesterday, save=True)
        revision(creator=u2, created=day_before_yesterday, save=True)

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
