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
            'product': self.product.slug,
            'topic': self.topic.slug,
        }

    def test_it_works(self):
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {})
        ok_(serializer.is_valid())

    def test_automatic_creator(self):
        del self.data['creator']
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {})
        ok_(serializer.is_valid())
        eq_(serializer.object.creator, self.user)

    def test_product_required(self):
        del self.data['product']
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {
            'product': [u'This field is required.'],
            'topic': [u'A product must be specified to select a topic.'],
        })
        ok_(not serializer.is_valid())

    def test_topic_required(self):
        del self.data['topic']
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {
            'topic': [u'This field is required.'],
        })
        ok_(not serializer.is_valid())

    def test_topic_disambiguation(self):
        # First make another product, and a colliding topic.
        # It has the same slug, but a different product.
        new_product = product(save=True)
        topic(product=new_product, slug=self.topic.slug, save=True)
        serializer = api.QuestionShortSerializer(
        topic(product=new_product, slug=self.topic.slug, save=True)
        serializer = api.QuestionShortSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {})
        ok_(serializer.is_valid())
        eq_(serializer.object.topic, self.topic)


class TestQuestionViewSet(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create(self):
        u = user(save=True)
        p = product(save=True)
        t = topic(product=p, save=True)
        self.client.force_authenticate(user=u)
        data = {
            'title': 'How do I start Firefox?',
            'content': 'Seriously, what do I do?',
            'product': p.slug,
            'topic': t.slug,
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

    def test_ordering(self):
        q1 = question(save=True)
        q2 = question(save=True)

        res = self.client.get(reverse('question-list'))
        eq_(res.data['results'][0]['id'], q2.id)
        eq_(res.data['results'][1]['id'], q1.id)

        res = self.client.get(reverse('question-list') + '?ordering=id')
        eq_(res.data['results'][0]['id'], q1.id)
        eq_(res.data['results'][1]['id'], q2.id)

        res = self.client.get(reverse('question-list') + '?ordering=-id')
        eq_(res.data['results'][0]['id'], q2.id)
        eq_(res.data['results'][1]['id'], q1.id)

    def test_filter_product_with_slug(self):
        p1 = product(save=True)
        p2 = product(save=True)
        q1 = question(product=p1, save=True)
        question(product=p2, save=True)

        querystring = '?product={0}'.format(p1.slug)
        res = self.client.get(reverse('question-list') + querystring)
        eq_(len(res.data['results']), 1)
        eq_(res.data['results'][0]['id'], q1.id)

    def test_filter_creator_with_username(self):
        q1 = question(save=True)
        question(save=True)

        querystring = '?creator={0}'.format(q1.creator.username)
        res = self.client.get(reverse('question-list') + querystring)
        eq_(len(res.data['results']), 1)
        eq_(res.data['results'][0]['id'], q1.id)


class TestAnswerViewSet(TestCase):

    def setUp(self):
        self.client = APIClient()

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

    def test_ordering(self):
        a1 = answer(save=True)
        a2 = answer(save=True)

        res = self.client.get(reverse('answer-list'))
        eq_(res.data['results'][0]['id'], a2.id)
        eq_(res.data['results'][1]['id'], a1.id)

        res = self.client.get(reverse('answer-list') + '?ordering=id')
        eq_(res.data['results'][0]['id'], a1.id)
        eq_(res.data['results'][1]['id'], a2.id)

        res = self.client.get(reverse('answer-list') + '?ordering=-id')
        eq_(res.data['results'][0]['id'], a2.id)
        eq_(res.data['results'][1]['id'], a1.id)
