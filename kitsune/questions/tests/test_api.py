import mock
from nose.tools import eq_, ok_

from rest_framework.test import APIClient

from kitsune.sumo.tests import TestCase
from kitsune.questions import api
from kitsune.questions.models import Question, Answer
from kitsune.questions.tests import question, answer
from kitsune.users.tests import profile, user
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

    def setUp(self):
        self.client = APIClient()

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
        u = user(save=True)
        p = product(save=True)
        t = topic(product=p, save=True)
        self.client.force_authenticate(user=u)
        data = {
            'title': 'How do I start Firefox?',
            'content': 'Seriously, what do I do?',
            'products': [p.slug],
            'topics': [t.slug],
        }
        eq_(Question.objects.count(), 0)
        res = self.client.post(reverse('question-list'), data)
        eq_(res.status_code, 201)
        eq_(Question.objects.count(), 1)
        q = Question.objects.all()[0]
        eq_(q.title, data['title'])
        eq_(q.content, data['content'])

    def test_delete_permissions(self):
        u1 = user(save=True)
        u2 = user(save=True)
        q = question(creator=u1, save=True)

        # Anonymous user can't delete
        self.client.force_authenticate(user=None)
        res = self.client.delete(reverse('question-detail', args=[q.id]))
        eq_(res.status_code, 401)  # Unauthorized

        # Non-owner can't delete
        self.client.force_authenticate(user=u2)
        res = self.client.delete(reverse('question-detail', args=[q.id]))
        eq_(res.status_code, 403)  # Forbidden

        # Owner can delete
        self.client.force_authenticate(user=u1)
        res = self.client.delete(reverse('question-detail', args=[q.id]))
        eq_(res.status_code, 204)  # No content

    def test_solve(self):
        q = question(save=True)
        a = answer(question=q, save=True)

        self.client.force_authenticate(user=q.creator)
        res = self.client.post(reverse('question-solve', args=[q.id]),
                               data={'answer': a.id})
        eq_(res.status_code, 204)
        q = Question.objects.get(id=q.id)
        eq_(q.solution, a)


class TestAnswerViewSet(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_short_serializer_used_for_lists(self):
        answer(save=True)
        res = self.client.get(reverse('answer-list'))
        eq_(res.status_code, 200)
        # The short serializer should not include the content field.
        assert 'content' not in res.data['results'][0]

    def test_detail_serializer_used_for_details(self):
        """The detail serializer should be used for detail views."""
        a = answer(save=True)
        res = self.client.get(reverse('answer-detail', args=[a.id]))
        eq_(res.status_code, 200)
        # The long serializer should include the content field.
        assert 'content' in res.data

    def test_create(self):
        q = question(save=True)
        u = user(save=True)
        self.client.force_authenticate(user=u)
        data = {
            'question': q.id,
            'content': 'You just need to click the fox.',
        }
        eq_(Answer.objects.count(), 0)
        res = self.client.post(reverse('answer-list'), data)
        eq_(res.status_code, 201)
        eq_(Answer.objects.count(), 1)
        a = Answer.objects.all()[0]
        eq_(a.content, data['content'])
        eq_(a.question, q)

    def test_delete_permissions(self):
        u1 = user(save=True)
        u2 = user(save=True)
        a = answer(creator=u1, save=True)

        # Anonymous user can't delete
        self.client.force_authenticate(user=None)
        res = self.client.delete(reverse('answer-detail', args=[a.id]))
        eq_(res.status_code, 401)  # Unauthorized

        # Non-owner can't deletea
        self.client.force_authenticate(user=u2)
        res = self.client.delete(reverse('answer-detail', args=[a.id]))
        eq_(res.status_code, 403)  # Forbidden

        # Owner can delete
        self.client.force_authenticate(user=u1)
        res = self.client.delete(reverse('answer-detail', args=[a.id]))
        eq_(res.status_code, 204)  # No content
