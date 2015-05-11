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
from kitsune.questions.tests import question, answer, questionvote, answervote
from kitsune.products.tests import product, topic
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.helpers import profile_avatar
from kitsune.users.models import Profile
from kitsune.users.tests import profile, user, add_permission


class TestQuestionSerializerDeserialization(TestCase):

    def setUp(self):
        self.profile = profile()
        self.product = product(save=True)
        self.topic = topic(product=self.product, save=True)
        self.request = mock.Mock()
        self.request.user = self.profile.user
        self.context = {
            'request': self.request,
        }
        self.data = {
            'creator': self.profile,
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
        eq_(serializer.object.creator, self.profile.user)

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
        serializer = api.QuestionSerializer(
            context=self.context, data=self.data)
        eq_(serializer.errors, {})
        ok_(serializer.is_valid())
        eq_(serializer.object.topic, self.topic)

    def test_solution_is_readonly(self):
        q = question(save=True)
        a = answer(question=q, save=True)
        self.data['solution'] = a.id
        serializer = api.QuestionSerializer(context=self.context, data=self.data, instance=q)
        serializer.save()
        eq_(q.solution, None)


class TestQuestionSerializerSerialization(TestCase):

    def setUp(self):
        self.asker = profile().user
        self.helper1 = profile().user
        self.helper2 = profile().user
        self.question = question(creator=self.asker, save=True)

    def _names(self, *users):
        return sorted(
            {
                'username': u.username,
                'display_name': Profile.objects.get(user=u).name,
                'avatar': profile_avatar(u),
            }
            for u in users)

    def _answer(self, user):
        return answer(question=self.question, creator=user, save=True)

    def test_no_votes(self):
        serializer = api.QuestionSerializer(instance=self.question)
        eq_(serializer.data['num_votes'], 0)

    def test_with_votes(self):
        questionvote(question=self.question, save=True)
        questionvote(question=self.question, save=True)
        questionvote(save=True)
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


class TestQuestionViewSet(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create(self):
        u = profile().user
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
        eq_(q.content_parsed, res.data['content'])

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

    def test_filter_is_taken_true(self):
        q1 = question(save=True)
        q2 = question(save=True)
        q2.take(q1.creator)

        url = reverse('question-list') + '?is_taken=1'
        res = self.client.get(url)

        eq_(res.status_code, 200)
        eq_(res.data['count'], 1)
        eq_(res.data['results'][0]['id'], q2.id)

    def test_filter_is_taken_false(self):
        q1 = question(save=True)
        q2 = question(save=True)
        q2.take(q1.creator)

        url = reverse('question-list') + '?is_taken=0'
        res = self.client.get(url)

        eq_(res.status_code, 200)
        eq_(res.data['count'], 1)
        eq_(res.data['results'][0]['id'], q1.id)

    def test_filter_is_taken_expired(self):
        q = question(save=True)
        # "take" the question, but with an expired timer.
        q.taken_by = profile().user
        q.taken_until = datetime.now() - timedelta(seconds=60)

        url = reverse('question-list') + '?is_taken=1'
        res = self.client.get(url)

        eq_(res.status_code, 200)
        eq_(res.data['count'], 0)

    def test_filter_taken_by_username(self):
        q1 = question(save=True)
        q2 = question(save=True)
        q2.take(q1.creator)

        url = reverse('question-list') + '?taken_by=' + q1.creator.username
        res = self.client.get(url)

        eq_(res.status_code, 200)
        eq_(res.data['count'], 1)
        eq_(res.data['results'][0]['id'], q2.id)

    def test_helpful(self):
        q = question(save=True)
        u = profile().user
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-helpful', args=[q.id]))
        eq_(res.status_code, 200)
        eq_(res.data, {'num_votes': 1})
        eq_(Question.objects.get(id=q.id).num_votes, 1)

    def test_helpful_double_vote(self):
        q = question(save=True)
        u = profile().user
        questionvote(question=q, creator=u, save=True)
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-helpful', args=[q.id]))
        eq_(res.status_code, 409)
        # It's 1, not 0, because one was created above. The failure cause is
        # if the number of votes is 2, one from above and one from the api call.
        eq_(Question.objects.get(id=q.id).num_votes, 1)

    def test_helpful_question_not_editable(self):
        q = question(is_locked=True, save=True)
        u = profile().user
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-helpful', args=[q.id]))
        eq_(res.status_code, 403)
        eq_(Question.objects.get(id=q.id).num_votes, 0)

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
        eq_(res.status_code, 200)
        eq_(len(res.data['results']), 1)
        eq_(res.data['results'][0]['id'], q1.id)

    def test_filter_involved(self):
        q1 = question(save=True)
        a1 = answer(question=q1, save=True)
        q2 = question(creator=a1.creator, save=True)

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
        q = question(save=True)
        u = profile().user
        q.take(u)
        url = reverse('question-detail', args=[q.id])
        res = self.client.get(url)
        eq_(res.status_code, 200)
        eq_(res.data['taken_by']['username'], u.username)

    def test_take(self):
        q = question(save=True)
        u = user(save=True)
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-take', args=[q.id]))
        eq_(res.status_code, 204)
        q = Question.objects.get(id=q.id)
        eq_(q.taken_by, u)

    def test_take_by_owner(self):
        q = question(save=True)
        self.client.force_authenticate(user=q.creator)
        res = self.client.post(reverse('question-take', args=[q.id]))
        eq_(res.status_code, 400)
        q = Question.objects.get(id=q.id)
        eq_(q.taken_by, None)

    def test_take_conflict(self):
        u1 = user(save=True)
        u2 = user(save=True)
        taken_until = datetime.now() + timedelta(seconds=30)
        q = question(save=True, taken_until=taken_until, taken_by=u1)
        self.client.force_authenticate(user=u2)
        res = self.client.post(reverse('question-take', args=[q.id]))
        eq_(res.status_code, 409)
        q = Question.objects.get(id=q.id)
        eq_(q.taken_by, u1)

    def test_follow(self):
        q = question(save=True)
        u = profile().user
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-follow', args=[q.id]))
        eq_(res.status_code, 204)
        f = Follow.objects.get(user=u)
        eq_(f.follow_object, q)
        eq_(f.actor_only, False)

    def test_unfollow(self):
        q = question(save=True)
        u = profile().user
        actstream.actions.follow(u, q, actor_only=False)
        eq_(Follow.objects.filter(user=u).count(), 1)  # pre-condition
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('question-unfollow', args=[q.id]))
        eq_(res.status_code, 204)
        eq_(Follow.objects.filter(user=u).count(), 0)

    def test_add_tags(self):
        q = question(save=True)
        eq_(0, q.tags.count())

        u = profile().user
        add_permission(u, Tag, 'add_tag')
        self.client.force_authenticate(user=u)

        res = self.client.post(reverse('question-add-tags', args=[q.id]),
                               content_type='application/json',
                               data=json.dumps({'tags': ['test', 'more', 'tags']}))
        eq_(res.status_code, 200)
        eq_(3, q.tags.count())

    def test_remove_tags(self):
        q = question(save=True)
        q.tags.add('test')
        q.tags.add('more')
        q.tags.add('tags')
        eq_(3, q.tags.count())

        u = profile().user
        self.client.force_authenticate(user=u)

        res = self.client.post(reverse('question-remove-tags', args=[q.id]),
                               content_type='application/json',
                               data=json.dumps({'tags': ['more', 'tags']}))
        eq_(res.status_code, 204)
        eq_(1, q.tags.count())

    def test_bleaching(self):
        """Tests whether question content is bleached."""
        q = question(content=u'<unbleached>Cupcakes are the best</unbleached>', save=True)
        url = reverse('question-detail', args=[q.id])
        res = self.client.get(url)
        eq_(res.status_code, 200)
        assert '<unbleached>' not in res.data['content']


class TestAnswerSerializerDeserialization(TestCase):

    def test_no_votes(self):
        a = answer(save=True)
        serializer = api.AnswerSerializer(instance=a)
        eq_(serializer.data['num_helpful_votes'], 0)
        eq_(serializer.data['num_unhelpful_votes'], 0)

    def test_with_votes(self):
        a = answer(save=True)
        answervote(answer=a, helpful=True, save=True)
        answervote(answer=a, helpful=True, save=True)
        answervote(answer=a, helpful=False, save=True)
        answervote(save=True)

        serializer = api.AnswerSerializer(instance=a)
        eq_(serializer.data['num_helpful_votes'], 2)
        eq_(serializer.data['num_unhelpful_votes'], 1)


class TestAnswerViewSet(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create(self):
        q = question(save=True)
        u = profile().user
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

    def test_helpful(self):
        a = answer(save=True)
        u = profile().user
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('answer-helpful', args=[a.id]))
        eq_(res.status_code, 200)
        eq_(res.data, {'num_helpful_votes': 1, 'num_unhelpful_votes': 0})
        eq_(Answer.objects.get(id=a.id).num_votes, 1)

    def test_helpful_double_vote(self):
        a = answer(save=True)
        u = profile().user
        answervote(answer=a, creator=u, save=True)
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('answer-helpful', args=[a.id]))
        eq_(res.status_code, 409)
        # It's 1, not 0, because one was created above. The failure cause is
        # if the number of votes is 2, one from above and one from the api call.
        eq_(Answer.objects.get(id=a.id).num_votes, 1)

    def test_helpful_answer_not_editable(self):
        q = question(is_locked=True, save=True)
        a = answer(question=q, save=True)
        u = profile().user
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('answer-helpful', args=[a.id]))
        eq_(res.status_code, 403)
        eq_(Answer.objects.get(id=a.id).num_votes, 0)

    def test_follow(self):
        a = answer(save=True)
        u = profile().user
        self.client.force_authenticate(user=u)
        eq_(Follow.objects.filter(user=u).count(), 0)  # pre-condition
        res = self.client.post(reverse('answer-follow', args=[a.id]))
        eq_(res.status_code, 204)
        f = Follow.objects.get(user=u)
        eq_(f.follow_object, a)
        eq_(f.actor_only, False)

    def test_unfollow(self):
        a = answer(save=True)
        u = profile().user
        actstream.actions.follow(u, a, actor_only=False)
        eq_(Follow.objects.filter(user=u).count(), 1)  # pre-condition
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse('answer-unfollow', args=[a.id]))
        eq_(res.status_code, 204)
        eq_(Follow.objects.filter(user=u).count(), 0)

    def test_bleaching(self):
        """Tests whether answer content is bleached."""
        a = answer(content=u'<unbleached>Cupcakes are the best</unbleached>', save=True)
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
        q1 = question(save=True)
        a1 = answer(question=q1, save=True)
        q2 = question(creator=a1.creator, save=True)

        qs = self.filter_instance.filter_involved(self.queryset, q1.creator.username)
        eq_(list(qs), [q1])

        qs = self.filter_instance.filter_involved(self.queryset, q2.creator.username)
        # The filter does not have a strong order.
        qs = sorted(qs, key=lambda q: q.id)
        eq_(qs, [q1, q2])

    def test_filter_is_solved(self):
        q1 = question(save=True)
        a1 = answer(question=q1, save=True)
        q1.solution = a1
        q1.save()
        q2 = question(save=True)

        qs = self.filter_instance.filter_is_solved(self.queryset, True)
        eq_(list(qs), [q1])

        qs = self.filter_instance.filter_is_solved(self.queryset, False)
        eq_(list(qs), [q2])

    def test_filter_solved_by(self):
        q1 = question(save=True)
        a1 = answer(question=q1, save=True)
        q1.solution = a1
        q1.save()
        q2 = question(save=True)
        answer(question=q2, creator=a1.creator, save=True)
        q3 = question(save=True)
        a3 = answer(question=q3, save=True)
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
        q1 = question(metadata={'os': 'Linux'}, save=True)
        question(metadata={'os': 'OSX'}, save=True)
        res = self.filter({'os': 'Linux'})
        eq_(list(res), [q1])

    def test_single_filter_no_match(self):
        question(metadata={'os': 'Linux'}, save=True)
        question(metadata={'os': 'OSX'}, save=True)
        res = self.filter({"os": "Windows 8"})
        eq_(list(res), [])

    def test_multi_filter_is_and(self):
        q1 = question(metadata={'os': 'Linux', 'category': 'troubleshooting'}, save=True)
        question(metadata={'os': 'OSX', 'category': 'troubleshooting'}, save=True)
        res = self.filter({'os': 'Linux', 'category': 'troubleshooting'})
        eq_(list(res), [q1])

    def test_list_value_is_or(self):
        q1 = question(metadata={'os': 'Linux'}, save=True)
        q2 = question(metadata={'os': 'OSX'}, save=True)
        question(metadata={'os': 'Windows 7'}, save=True)
        res = self.filter({'os': ['Linux', 'OSX']})
        eq_(sorted(res, key=lambda q: q.id), [q1, q2])

    def test_none_value_is_missing(self):
        q1 = question(metadata={}, save=True)
        question(metadata={'os': 'Linux'}, save=True)
        res = self.filter({'os': None})
        eq_(list(res), [q1])

    def test_list_value_with_none(self):
        q1 = question(metadata={'os': 'Linux'}, save=True)
        q2 = question(metadata={}, save=True)
        question(metadata={'os': 'Windows 7'}, save=True)
        res = self.filter({'os': ['Linux', None]})
        eq_(sorted(res, key=lambda q: q.id), [q1, q2])

    def test_is_taken(self):
        u = user(save=True)
        taken_until = datetime.now() + timedelta(seconds=30)
        q = question(taken_by=u, taken_until=taken_until, save=True)
        question(save=True)
        res = self.filter_instance.filter_is_taken(self.queryset, True)
        eq_(list(res), [q])

    def test_is_not_taken(self):
        u = user(save=True)
        taken_until = datetime.now() + timedelta(seconds=30)
        question(taken_by=u, taken_until=taken_until, save=True)
        q = question(save=True)
        res = self.filter_instance.filter_is_taken(self.queryset, False)
        eq_(list(res), [q])

    def test_is_taken_expired(self):
        u = user(save=True)
        taken_until = datetime.now() - timedelta(seconds=30)
        question(taken_by=u, taken_until=taken_until, save=True)
        res = self.filter_instance.filter_is_taken(self.queryset, True)
        eq_(list(res), [])

    def test_is_not_taken_expired(self):
        u = user(save=True)
        taken_until = datetime.now() - timedelta(seconds=30)
        q = question(taken_by=u, taken_until=taken_until, save=True)
        res = self.filter_instance.filter_is_taken(self.queryset, False)
        eq_(list(res), [q])

    def test_it_works_with_users_who_have_gotten_first_contrib_emails(self):
        # Yes, really.
        u = profile(first_answer_email_sent=True).user
        question(creator=u, save=True)
        url = reverse('question-list')
        res = self.client.get(url)
        eq_(res.status_code, 200)
