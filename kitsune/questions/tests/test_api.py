import mock
from nose.tools import eq_, ok_

from kitsune.sumo.tests import TestCase
from kitsune.questions import api
from kitsune.questions.models import Question
from kitsune.questions.tests import question
from kitsune.users.tests import profile
from kitsune.products.tests import product, topic
from kitsune.sumo.urlresolvers import reverse


class TestQuestionSerializer(TestCase):

    def setUp(self):
        self.profile = profile()
        self.user = self.profile.user
        self.product = product(save=True)
        self.topic = topic(product=self.product, save=True)
        self.request = mock.Mock()
        self.request.user = self.user
        self.context = {
            'request': self.request,
        }
        self.data = {
            'creator': self.user,
            'title': 'How do I test programs?',
            'content': "Help, I don't know what to do.",
            'products': [self.product.slug],
            'topics': [self.topic.slug],
        }

    def test_automatic_creator(self):
        del self.data['creator']
        serializer = api.QuestionShortSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {})
        ok_(serializer.is_valid())
        eq_(serializer.object.creator, self.user)

    def test_products_required_empty_list(self):
        self.data['products'] = []
        serializer = api.QuestionShortSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {
            'products': [u'At least one required.'],
        })
        ok_(not serializer.is_valid())

    def test_products_required_missing(self):
        del self.data['products']
        serializer = api.QuestionShortSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {
            'products': [u'At least one required.'],
        })
        ok_(not serializer.is_valid())

    def test_topics_required_empty_list(self):
        self.data['topics'] = []
        serializer = api.QuestionShortSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {
            'topics': [u'At least one required.'],
        })
        ok_(not serializer.is_valid())

    def test_topics_required_missing(self):
        del self.data['topics']
        serializer = api.QuestionShortSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {
            'topics': [u'At least one required.'],
        })
        ok_(not serializer.is_valid())


class TestQuestionViewSet(TestCase):

    def test_short_serializer_used_for_lists(self):
        question(save=True)
        res = self.client.get(reverse('question-list'))
        eq_(res.status_code, 200)
        # The short serializer should not include the content field.
        assert 'content' not in res.data['results'][0]

    def test_detail_serializer_used_for_details(self):
        """The detail serializer should be used for detail views."""
        q = question(save=True)
        res = self.client.get(reverse('question-detail', args=[q.id]))
        eq_(res.status_code, 200)
        # The long serializer should include the content field.
        assert 'content' in res.data

    def test_create(self):
        data = {
            'title': 'How do I start Firefox?',
            'content': 'Seriously, what do I do?',
        }
        eq_(Question.objects.count(), 0)
        res = self.client.post(reverse('question-list'), data)
        eq_(res.status_code, 200)
        eq_(Question.objects.count(), 1)
        q = Question.objects.all()[0]
        eq_(q.title, data['title'])
        eq_(q.content, data['content'])
