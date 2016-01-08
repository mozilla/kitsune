import json
from datetime import datetime, timedelta

import mock
import actstream.actions
from actstream.models import Follow
from nose.tools import eq_, ok_, raises
from rest_framework.test import APIClient
from rest_framework.exceptions import APIException
from taggit.models import Tag

from kitsune.sumo.tests import TestCase
from kitsune.questions import api
from kitsune.questions.models import Question, Answer
from kitsune.questions.tests import (
    tags_eq, QuestionFactory, AnswerFactory, QuestionVoteFactory, AnswerVoteFactory)
from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.sumo.urlresolvers import reverse
from kitsune.tags.tests import TagFactory
from kitsune.users.templatetags.jinja_helpers import profile_avatar
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory, add_permission


class TestQuestionSerializerDeserialization(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory()
        self.topic = TopicFactory(product=self.product)
        self.request = mock.Mock()
        self.request.user = self.user
        self.context = {
            'request': self.request,
        }
        self.data = {
            'creator': self.user.profile,
            'title': 'How do I test programs?',
            'content': "Help, I don't know what to do.",
            'product': self.product.slug,
            'topic': self.topic.slug,
        }

    def test_it_works(self):
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        serializer.is_valid(raise_exception=True)

    def test_automatic_creator(self):
        del self.data['creator']
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        eq_(obj.creator, self.user)

    def test_product_required(self):
        del self.data['product']
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        ok_(not serializer.is_valid())
        eq_(serializer.errors, {
            'product': [u'This field is required.'],
            'topic': [u'A product must be specified to select a topic.'],
        })

    def test_topic_required(self):
        del self.data['topic']
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        ok_(not serializer.is_valid())
        eq_(serializer.errors, {
            'topic': [u'This field is required.'],
        })

    def test_topic_disambiguation(self):
        # First make another product, and a colliding topic.
        # It has the same slug, but a different product.
        new_product = ProductFactory()
        TopicFactory(product=new_product, slug=self.topic.slug)
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        eq_(obj.topic, self.topic)

    def test_solution_is_readonly(self):
        q = QuestionFactory()
        a = AnswerFactory(question=q)
        self.data['solution'] = a.id
        serializer = api.QuestionSerializer(context=self.context, data=self.data, instance=q)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        eq_(q.solution, None)


class TestQuestionSerializerSerialization(TestCase):

    def setUp(self):
        self.asker = UserFactory()
        self.helper1 = UserFactory()
        self.helper2 = UserFactory()
        self.question = QuestionFactory(creator=self.asker)

    def _names(self, *users):
        return sorted(
            {
                'username': u.username,
                'display_name': Profile.objects.get(user=u).name,
                'avatar': profile_avatar(u),
            }
            for u in users)

    def _answer(self, user):
        return AnswerFactory(question=self.question, creator=user)

    def test_no_votes(self):
        serializer = api.QuestionSerializer(instance=self.question)
        eq_(serializer.data['num_votes'], 0)

    def test_with_votes(self):
        QuestionVoteFactory(question=self.question)
        QuestionVoteFactory(question=self.question)
        QuestionVoteFactory()
        serializer = api.QuestionSerializer(instance=self.question)
        eq_(serializer.data['num_votes'], 2)

    def test_just_asker(self):
        serializer = api.QuestionSerializer(instance=self.question)
        eq_(serializer.data['involved'], self._names(self.asker))

    def test_one_answer(self):
        self._answer(self.helper1)

        serializer = api.QuestionSerializer(instance=self.question)
        eq_(sorted(serializer.data['involved']), self._names(self.asker, self.helper1))

    def test_asker_and_response(self):
        self._answer(self.helper1)
        self._answer(self.asker)

        serializer = api.QuestionSerializer(instance=self.question)
        eq_(sorted(serializer.data['involved']), self._names(self.asker, self.helper1))

    def test_asker_and_two_answers(self):
        self._answer(self.helper1)
        self._answer(self.asker)
        self._answer(self.helper2)

        serializer = api.QuestionSerializer(instance=self.question)
        eq_(sorted(serializer.data['involved']),
            self._names(self.asker, self.helper1, self.helper2))

    def test_solution_is_id(self):
        a = self._answer(self.helper1)
        self.question.solution = a
        self.question.save()

        serializer = api.QuestionSerializer(instance=self.question)
        eq_(serializer.data['solution'], a.id)

    def test_creator_is_object(self):
        serializer = api.QuestionSerializer(instance=self.question)
        eq_(serializer.data['creator'], {
            'username': self.question.creator.username,
            'display_name': Profile.objects.get(user=self.question.creator).display_name,
            'avatar': profile_avatar(self.question.creator),
        })

    def test_with_tags(self):
        self.question.tags.add('tag1')
        self.question.tags.add('tag2')
        serializer = api.QuestionSerializer(instance=self.question)
        eq_(serializer.data['tags'], [
            {'name': 'tag1', 'slug': 'tag1'},
            {'name': 'tag2', 'slug': 'tag2'},
        ])


class TestQuestionViewSet(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create(self):
        u = UserFactory()
        p = ProductFactory()
        t = TopicFactory(product=p)
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
        eq_(q.content_parsed, res.data['content'])

    def test_delete_permissions(self):
        u1 = UserFactory()
        u2 = UserFactory()
        q = QuestionFactory(creator=u1)

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
        q = QuestionFactory()
        a = AnswerFactory(question=q)

        self.client.force_authenticate(user=q.creator)
        res = self.client.post(reverse('question-solve', args=[q.id]),
                               data={'answer': a.id})
        eq_(res.status_code, 204)
        q = Question.objects.get(id=q.id)
        eq_(q.solution, a)

    def test_filter_is_taken_true(self):
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        q2.take(q1.creator)

        url = reverse('question-list') + '?is_taken=1'
        res = self.client.get(url)

        eq_(res.status_code, 200)
        eq_(res.data['count'], 1)
        eq_(res.data['results'][0]['id'], q2.id)

    def test_filter_is_taken_false(self):
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        q2.take(q1.creator)

        url = reverse('question-list') + '?is_taken=0'
        res = self.client.get(url)

        eq_(res.status_code, 200)
        eq_(res.data['count'], 1)
        eq_(res.data['results'][0]['id'], q1.id)

    def test_filter_is_taken_expired(self):
        q = QuestionFactory()
        # "take" the question, but with an expired timer.
        q.taken_by = UserFactory()
        q.taken_until = datetime.now() - timedelta(seconds=60)

        url = reverse('question-list') + '?is_taken=1'
        res = self.client.get(url)

        eq_(res.status_code, 200)
        eq_(res.data['count'], 0)

    def test_filter_taken_by_username(self):
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        q2.take(q1.creator)

        url = reverse('question-list') + '?taken_by=' + q1.creator.username
        res = self.client.get(url)

        eq_(res.status_code, 200)
        eq_(res.data['count'], 1)
        eq_(res.data['results'][0]['id'], q2.id)

    def test_helpful(self):
        q = QuestionFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-helpful', args=[q.id]))
        eq_(res.status_code, 200)
        eq_(res.data, {'num_votes': 1})
        eq_(Question.objects.get(id=q.id).num_votes, 1)

    def test_helpful_double_vote(self):
        q = QuestionFactory()
        u = UserFactory()
        QuestionVoteFactory(question=q, creator=u)
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-helpful', args=[q.id]))
        eq_(res.status_code, 409)
        # It's 1, not 0, because one was created above. The failure cause is
        # if the number of votes is 2, one from above and one from the api call.
        eq_(Question.objects.get(id=q.id).num_votes, 1)

    def test_helpful_question_not_editable(self):
        q = QuestionFactory(is_locked=True)
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-helpful', args=[q.id]))
        eq_(res.status_code, 403)
        eq_(Question.objects.get(id=q.id).num_votes, 0)

    def test_ordering(self):
        q1 = QuestionFactory()
        q2 = QuestionFactory()

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
        p1 = ProductFactory()
        p2 = ProductFactory()
        q1 = QuestionFactory(product=p1)
        QuestionFactory(product=p2)

        querystring = '?product={0}'.format(p1.slug)
        res = self.client.get(reverse('question-list') + querystring)
        eq_(len(res.data['results']), 1)
        eq_(res.data['results'][0]['id'], q1.id)

    def test_filter_creator_with_username(self):
        q1 = QuestionFactory()
        QuestionFactory()

        querystring = '?creator={0}'.format(q1.creator.username)
        res = self.client.get(reverse('question-list') + querystring)
        eq_(res.status_code, 200)
        eq_(len(res.data['results']), 1)
        eq_(res.data['results'][0]['id'], q1.id)

    def test_filter_involved(self):
        q1 = QuestionFactory()
        a1 = AnswerFactory(question=q1)
        q2 = QuestionFactory(creator=a1.creator)

        querystring = '?involved={0}'.format(q1.creator.username)
        res = self.client.get(reverse('question-list') + querystring)
        eq_(res.status_code, 200)
        eq_(len(res.data['results']), 1)
        eq_(res.data['results'][0]['id'], q1.id)

        querystring = '?involved={0}'.format(q2.creator.username)
        res = self.client.get(reverse('question-list') + querystring)
        eq_(res.status_code, 200)
        eq_(len(res.data['results']), 2)
        # The API has a default sort, so ordering will be consistent.
        eq_(res.data['results'][0]['id'], q2.id)
        eq_(res.data['results'][1]['id'], q1.id)

    def test_is_taken(self):
        q = QuestionFactory()
        u = UserFactory()
        q.take(u)
        url = reverse('question-detail', args=[q.id])
        res = self.client.get(url)
        eq_(res.status_code, 200)
        eq_(res.data['taken_by']['username'], u.username)

    def test_take(self):
        q = QuestionFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-take', args=[q.id]))
        eq_(res.status_code, 204)
        q = Question.objects.get(id=q.id)
        eq_(q.taken_by, u)

    def test_take_by_owner(self):
        q = QuestionFactory()
        self.client.force_authenticate(user=q.creator)
        res = self.client.post(reverse('question-take', args=[q.id]))
        eq_(res.status_code, 400)
        q = Question.objects.get(id=q.id)
        eq_(q.taken_by, None)

    def test_take_conflict(self):
        u1 = UserFactory()
        u2 = UserFactory()
        taken_until = datetime.now() + timedelta(seconds=30)
        q = QuestionFactory(taken_until=taken_until, taken_by=u1)
        self.client.force_authenticate(user=u2)
        res = self.client.post(reverse('question-take', args=[q.id]))
        eq_(res.status_code, 409)
        q = Question.objects.get(id=q.id)
        eq_(q.taken_by, u1)

    def test_follow(self):
        q = QuestionFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-follow', args=[q.id]))
        eq_(res.status_code, 204)
        f = Follow.objects.get(user=u)
        eq_(f.follow_object, q)
        eq_(f.actor_only, False)

    def test_unfollow(self):
        q = QuestionFactory()
        u = UserFactory()
        actstream.actions.follow(u, q, actor_only=False)
        eq_(Follow.objects.filter(user=u).count(), 1)  # pre-condition
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-unfollow', args=[q.id]))
        eq_(res.status_code, 204)
        eq_(Follow.objects.filter(user=u).count(), 0)

    def test_add_tags(self):
        q = QuestionFactory()
        eq_(0, q.tags.count())

        u = UserFactory()
        add_permission(u, Tag, 'add_tag')
        self.client.force_authenticate(user=u)

        res = self.client.post(reverse('question-add-tags', args=[q.id]),
                               content_type='application/json',
                               data=json.dumps({'tags': ['test', 'more', 'tags']}))
        eq_(res.status_code, 200)
        eq_(3, q.tags.count())

    def test_remove_tags(self):
        q = QuestionFactory()
        q.tags.add('test')
        q.tags.add('more')
        q.tags.add('tags')
        eq_(3, q.tags.count())

        u = UserFactory()
        self.client.force_authenticate(user=u)

        res = self.client.post(reverse('question-remove-tags', args=[q.id]),
                               content_type='application/json',
                               data=json.dumps({'tags': ['more', 'tags']}))
        eq_(res.status_code, 204)
        eq_(1, q.tags.count())

    def test_bleaching(self):
        """Tests whether question content is bleached."""
        q = QuestionFactory(content=u'<unbleached>Cupcakes are the best</unbleached>')
        url = reverse('question-detail', args=[q.id])
        res = self.client.get(url)
        eq_(res.status_code, 200)
        assert '<unbleached>' not in res.data['content']

    def test_auto_tagging(self):
        """Test that questions created via the API are auto-tagged."""
        TagFactory(name='desktop')
        q = QuestionFactory()
        self.client.force_authenticate(user=q.creator)
        tags_eq(q, [])

        res = self.client.post(
            reverse('question-set-metadata', args=[q.id]),
            content_type='application/json',
            data=json.dumps({'name': 'product', 'value': 'desktop'}))
        eq_(res.status_code, 200)
        tags_eq(q, [])

        res = self.client.post(
            reverse('question-auto-tag', args=[q.id]),
            content_type='application/json')
        eq_(res.status_code, 204)
        tags_eq(q, ['desktop'])


class TestAnswerSerializerDeserialization(TestCase):

    def test_no_votes(self):
        a = AnswerFactory()
        serializer = api.AnswerSerializer(instance=a)
        eq_(serializer.data['num_helpful_votes'], 0)
        eq_(serializer.data['num_unhelpful_votes'], 0)

    def test_with_votes(self):
        a = AnswerFactory()
        AnswerVoteFactory(answer=a, helpful=True)
        AnswerVoteFactory(answer=a, helpful=True)
        AnswerVoteFactory(answer=a, helpful=False)
        AnswerVoteFactory()

        serializer = api.AnswerSerializer(instance=a)
        eq_(serializer.data['num_helpful_votes'], 2)
        eq_(serializer.data['num_unhelpful_votes'], 1)


class TestAnswerViewSet(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create(self):
        q = QuestionFactory()
        u = UserFactory()
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
        eq_(a.content_parsed, res.data['content'])
        eq_(a.question, q)

    def test_delete_permissions(self):
        u1 = UserFactory()
        u2 = UserFactory()
        a = AnswerFactory(creator=u1)

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
        a1 = AnswerFactory()
        a2 = AnswerFactory()

        res = self.client.get(reverse('answer-list'))
        eq_(res.data['results'][0]['id'], a2.id)
        eq_(res.data['results'][1]['id'], a1.id)

        res = self.client.get(reverse('answer-list') + '?ordering=id')
        eq_(res.data['results'][0]['id'], a1.id)
        eq_(res.data['results'][1]['id'], a2.id)

        res = self.client.get(reverse('answer-list') + '?ordering=-id')
        eq_(res.data['results'][0]['id'], a2.id)
        eq_(res.data['results'][1]['id'], a1.id)

    def test_helpful(self):
        a = AnswerFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('answer-helpful', args=[a.id]))
        eq_(res.status_code, 200)
        eq_(res.data, {'num_helpful_votes': 1, 'num_unhelpful_votes': 0})
        eq_(Answer.objects.get(id=a.id).num_votes, 1)

    def test_helpful_double_vote(self):
        a = AnswerFactory()
        u = UserFactory()
        AnswerVoteFactory(answer=a, creator=u)
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('answer-helpful', args=[a.id]))
        eq_(res.status_code, 409)
        # It's 1, not 0, because one was created above. The failure cause is
        # if the number of votes is 2, one from above and one from the api call.
        eq_(Answer.objects.get(id=a.id).num_votes, 1)

    def test_helpful_answer_not_editable(self):
        q = QuestionFactory(is_locked=True)
        a = AnswerFactory(question=q)
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('answer-helpful', args=[a.id]))
        eq_(res.status_code, 403)
        eq_(Answer.objects.get(id=a.id).num_votes, 0)

    def test_follow(self):
        a = AnswerFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        eq_(Follow.objects.filter(user=u).count(), 0)  # pre-condition
        res = self.client.post(reverse('answer-follow', args=[a.id]))
        eq_(res.status_code, 204)
        f = Follow.objects.get(user=u)
        eq_(f.follow_object, a)
        eq_(f.actor_only, False)

    def test_unfollow(self):
        a = AnswerFactory()
        u = UserFactory()
        actstream.actions.follow(u, a, actor_only=False)
        eq_(Follow.objects.filter(user=u).count(), 1)  # pre-condition
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('answer-unfollow', args=[a.id]))
        eq_(res.status_code, 204)
        eq_(Follow.objects.filter(user=u).count(), 0)

    def test_bleaching(self):
        """Tests whether answer content is bleached."""
        a = AnswerFactory(content=u'<unbleached>Cupcakes are the best</unbleached>')
        url = reverse('answer-detail', args=[a.id])
        res = self.client.get(url)
        eq_(res.status_code, 200)
        assert '<unbleached>' not in res.data['content']


class TestQuestionFilter(TestCase):

    def setUp(self):
        self.filter_instance = api.QuestionFilter()
        self.queryset = Question.objects.all()

    def filter(self, filter_data):
        return self.filter_instance.filter_metadata(self.queryset, json.dumps(filter_data))

    def test_filter_involved(self):
        q1 = QuestionFactory()
        a1 = AnswerFactory(question=q1)
        q2 = QuestionFactory(creator=a1.creator)

        qs = self.filter_instance.filter_involved(self.queryset, q1.creator.username)
        eq_(list(qs), [q1])

        qs = self.filter_instance.filter_involved(self.queryset, q2.creator.username)
        # The filter does not have a strong order.
        qs = sorted(qs, key=lambda q: q.id)
        eq_(qs, [q1, q2])

    def test_filter_is_solved(self):
        q1 = QuestionFactory()
        a1 = AnswerFactory(question=q1)
        q1.solution = a1
        q1.save()
        q2 = QuestionFactory()

        qs = self.filter_instance.filter_is_solved(self.queryset, True)
        eq_(list(qs), [q1])

        qs = self.filter_instance.filter_is_solved(self.queryset, False)
        eq_(list(qs), [q2])

    def test_filter_solved_by(self):
        q1 = QuestionFactory()
        a1 = AnswerFactory(question=q1)
        q1.solution = a1
        q1.save()
        q2 = QuestionFactory()
        AnswerFactory(question=q2, creator=a1.creator)
        q3 = QuestionFactory()
        a3 = AnswerFactory(question=q3)
        q3.solution = a3
        q3.save()

        qs = self.filter_instance.filter_solved_by(self.queryset, a1.creator.username)
        eq_(list(qs), [q1])

        qs = self.filter_instance.filter_solved_by(self.queryset, a3.creator.username)
        eq_(list(qs), [q3])

    @raises(APIException)
    def test_metadata_not_json(self):
        self.filter_instance.filter_metadata(self.queryset, 'not json')

    @raises(APIException)
    def test_metadata_bad_json(self):
        self.filter_instance.filter_metadata(self.queryset, 'not json')

    def test_single_filter_match(self):
        q1 = QuestionFactory(metadata={'os': 'Linux'})
        QuestionFactory(metadata={'os': 'OSX'})
        res = self.filter({'os': 'Linux'})
        eq_(list(res), [q1])

    def test_single_filter_no_match(self):
        QuestionFactory(metadata={'os': 'Linux'})
        QuestionFactory(metadata={'os': 'OSX'})
        res = self.filter({"os": "Windows 8"})
        eq_(list(res), [])

    def test_multi_filter_is_and(self):
        q1 = QuestionFactory(metadata={'os': 'Linux', 'category': 'troubleshooting'})
        QuestionFactory(metadata={'os': 'OSX', 'category': 'troubleshooting'})
        res = self.filter({'os': 'Linux', 'category': 'troubleshooting'})
        eq_(list(res), [q1])

    def test_list_value_is_or(self):
        q1 = QuestionFactory(metadata={'os': 'Linux'})
        q2 = QuestionFactory(metadata={'os': 'OSX'})
        QuestionFactory(metadata={'os': 'Windows 7'})
        res = self.filter({'os': ['Linux', 'OSX']})
        eq_(sorted(res, key=lambda q: q.id), [q1, q2])

    def test_none_value_is_missing(self):
        q1 = QuestionFactory(metadata={})
        QuestionFactory(metadata={'os': 'Linux'})
        res = self.filter({'os': None})
        eq_(list(res), [q1])

    def test_list_value_with_none(self):
        q1 = QuestionFactory(metadata={'os': 'Linux'})
        q2 = QuestionFactory(metadata={})
        QuestionFactory(metadata={'os': 'Windows 7'})
        res = self.filter({'os': ['Linux', None]})
        eq_(sorted(res, key=lambda q: q.id), [q1, q2])

    def test_is_taken(self):
        u = UserFactory()
        taken_until = datetime.now() + timedelta(seconds=30)
        q = QuestionFactory(taken_by=u, taken_until=taken_until)
        QuestionFactory()
        res = self.filter_instance.filter_is_taken(self.queryset, True)
        eq_(list(res), [q])

    def test_is_not_taken(self):
        u = UserFactory()
        taken_until = datetime.now() + timedelta(seconds=30)
        QuestionFactory(taken_by=u, taken_until=taken_until)
        q = QuestionFactory()
        res = self.filter_instance.filter_is_taken(self.queryset, False)
        eq_(list(res), [q])

    def test_is_taken_expired(self):
        u = UserFactory()
        taken_until = datetime.now() - timedelta(seconds=30)
        QuestionFactory(taken_by=u, taken_until=taken_until)
        res = self.filter_instance.filter_is_taken(self.queryset, True)
        eq_(list(res), [])

    def test_is_not_taken_expired(self):
        u = UserFactory()
        taken_until = datetime.now() - timedelta(seconds=30)
        q = QuestionFactory(taken_by=u, taken_until=taken_until)
        res = self.filter_instance.filter_is_taken(self.queryset, False)
        eq_(list(res), [q])

    def test_it_works_with_users_who_have_gotten_first_contrib_emails(self):
        # This flag caused a regression, tracked in bug 1163855.
        # The error was that the help text on the field was a str instead of a
        # unicode. Yes, really, that matters apparently.
        u = UserFactory(profile__first_answer_email_sent=True)
        QuestionFactory(creator=u)
        url = reverse('question-list')
        res = self.client.get(url)
        eq_(res.status_code, 200)
