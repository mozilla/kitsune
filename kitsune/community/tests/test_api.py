from nose.tools import eq_, raises

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
