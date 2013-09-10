# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.db.models import Q

import mock
import waffle
from nose import SkipTest
from nose.tools import eq_, raises
from taggit.models import Tag

import kitsune.sumo.models
from kitsune.flagit.models import FlaggedObject
from kitsune.karma.manager import KarmaManager
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.questions.cron import auto_lock_old_questions
from kitsune.questions.events import QuestionReplyEvent
from kitsune.questions.karma_actions import SolutionAction, AnswerAction
from kitsune.questions.models import (
    Answer, Question, QuestionMetaData, QuestionVisits,
    _tenths_version, _has_beta, user_num_questions,
    user_num_answers, user_num_solutions)
from kitsune.questions.tasks import update_answer_pages
from kitsune.questions.tests import TestCaseBase, tags_eq, question, answer
from kitsune.questions.question_config import products
from kitsune.sumo import googleanalytics
from kitsune.sumo.tests import TestCase
from kitsune.tags.tests import tag
from kitsune.tags.utils import add_existing_tag
from kitsune.users.tests import user
from kitsune.wiki.tests import translated_revision


class TestAnswer(TestCaseBase):
    """Test the Answer model"""

    def test_new_answer_updates_question(self):
        """Test saving a new answer updates the corresponding question.
        Specifically, last_post and num_replies should update."""
        q = question(title='Test Question', content='Lorem Ipsum Dolor',
                     save=True)
        updated = q.updated

        eq_(0, q.num_answers)
        eq_(None, q.last_answer)

        a = answer(question=q, content='Test Answer', save=True)
        a.save()

        q = Question.objects.get(pk=q.id)
        eq_(1, q.num_answers)
        eq_(a, q.last_answer)
        self.assertNotEqual(updated, q.updated)

    def test_delete_question_removes_flag(self):
        """Deleting a question also removes the flags on that question."""
        q = question(title='Test Question', content='Lorem Ipsum Dolor',
                     save=True)

        u = user(save=True)
        FlaggedObject.objects.create(
            status=0, content_object=q, reason='language', creator_id=u.id)
        eq_(1, FlaggedObject.objects.count())

        q.delete()
        eq_(0, FlaggedObject.objects.count())

    def test_delete_answer_removes_flag(self):
        """Deleting an answer also removes the flags on that answer."""
        q = question(title='Test Question', content='Lorem Ipsum Dolor',
                     save=True)

        a = answer(question=q, content='Test Answer', save=True)

        u = user(save=True)
        FlaggedObject.objects.create(
            status=0, content_object=a, reason='language', creator_id=u.id)
        eq_(1, FlaggedObject.objects.count())

        a.delete()
        eq_(0, FlaggedObject.objects.count())

    def test_delete_last_answer_of_question(self):
        """Deleting the last_answer of a Question should update the question.
        """
        yesterday = datetime.now() - timedelta(days=1)
        q = answer(created=yesterday, save=True).question
        last_answer = q.last_answer

        # add a new answer and verify last_answer updated
        a = answer(question=q, content='Test Answer', save=True)
        q = Question.objects.get(pk=q.id)

        eq_(q.last_answer.id, a.id)

        # delete the answer and last_answer should go back to previous value
        a.delete()
        q = Question.objects.get(pk=q.id)
        eq_(q.last_answer.id, last_answer.id)
        eq_(Answer.objects.filter(pk=a.id).count(), 0)

    def test_delete_solution_of_question(self):
        """Deleting the solution of a Question should update the question.
        """
        # set a solution to the question
        q = answer(save=True).question
        solution = q.last_answer
        q.solution = solution
        q.save()

        # delete the solution and question.solution should go back to None
        solution.delete()
        q = Question.objects.get(pk=q.id)
        eq_(q.solution, None)

    def test_update_page_task(self):
        a = answer(save=True)
        a.page = 4
        a.save()
        a = Answer.objects.get(pk=a.id)
        assert a.page == 4
        update_answer_pages(a.question)
        a = Answer.objects.get(pk=a.id)
        assert a.page == 1

    def test_delete_updates_pages(self):
        a1 = answer(save=True)
        a2 = answer(question=a1.question, save=True)
        answer(question=a1.question, save=True)
        a1.page = 7
        a1.save()
        a2.delete()
        a3 = Answer.objects.filter(question=a1.question)[0]
        assert a3.page == 1, "Page was %s" % a3.page

    def test_creator_num_answers(self):
        a = answer(save=True)

        eq_(a.creator_num_answers, 1)

        answer(creator=a.creator, save=True)
        eq_(a.creator_num_answers, 2)

    def test_creator_num_solutions(self):
        a = answer(save=True)
        q = a.question

        q.solution = a
        q.save()

        eq_(a.creator_num_solutions, 1)

    @mock.patch.object(waffle, 'switch_is_active')
    def test_creator_nums_redis(self, switch_is_active):
        """Test creator_num_* pulled from karma data."""
        try:
            KarmaManager()
            redis_client('karma').flushdb()
        except RedisError:
            raise SkipTest

        switch_is_active.return_value = True
        a = answer(save=True)

        AnswerAction(a.creator).save()
        AnswerAction(a.creator).save()
        SolutionAction(a.creator).save()

        eq_(a.creator_num_solutions, 1)
        eq_(a.creator_num_answers, 3)

    def test_content_parsed_with_locale(self):
        """Make sure links to localized articles work."""
        rev = translated_revision(locale='es', is_approved=True, save=True)
        doc = rev.document
        doc.title = u'Un mejor título'
        doc.save()

        q = question(locale='es', save=True)
        a = answer(question=q, content='[[%s]]' % doc.title, save=True)

        assert 'es/kb/%s' % doc.slug in a.content_parsed


class TestQuestionMetadata(TestCaseBase):
    """Tests handling question metadata"""

    def setUp(self):
        super(TestQuestionMetadata, self).setUp()

        # add a new Question to test with
        self.question = question(
            title='Test Question', content='Lorem Ipsum Dolor', save=True)

    def test_add_metadata(self):
        """Test the saving of metadata."""
        metadata = {'version': u'3.6.3', 'os': u'Windows 7'}
        self.question.add_metadata(**metadata)
        saved = QuestionMetaData.objects.filter(question=self.question)
        eq_(dict((x.name, x.value) for x in saved), metadata)

    def test_metadata_property(self):
        """Test the metadata property on Question model."""
        self.question.add_metadata(crash_id='1234567890')
        eq_('1234567890', self.question.metadata['crash_id'])

    def test_product_property(self):
        """Test question.product property."""
        self.question.add_metadata(product='desktop')
        eq_(products['desktop'], self.question.product)

    def test_category_property(self):
        """Test question.category property."""
        self.question.add_metadata(product='desktop')
        self.question.add_metadata(category='fix-problems')
        eq_(products['desktop']['categories']['fix-problems'],
            self.question.category)

    def test_clear_mutable_metadata(self):
        """Make sure it works and clears the internal cache.

        crash_id should get cleared, while product, category, and useragent
        should remain.

        """
        q = self.question
        q.add_metadata(product='desktop', category='fix-problems',
                       useragent='Fyerfocks', crash_id='7')

        q.metadata
        q.clear_mutable_metadata()
        md = q.metadata
        assert 'crash_id' not in md, \
            "clear_mutable_metadata() didn't clear the cached metadata."
        eq_(dict(product='desktop', category='fix-problems',
                 useragent='Fyerfocks'),
            md)

    def test_auto_tagging(self):
        """Make sure tags get applied based on metadata on first save."""
        Tag.objects.create(slug='green', name='green')
        Tag.objects.create(slug='Fix problems', name='fix-problems')
        q = self.question
        q.add_metadata(product='desktop', category='fix-problems',
                       ff_version='3.6.8', os='GREen')
        q.save()
        q.auto_tag()
        tags_eq(q, ['desktop', 'fix-problems', 'Firefox 3.6.8', 'Firefox 3.6',
                    'green'])

    def test_auto_tagging_aurora(self):
        """Make sure versions with prerelease suffix are tagged properly."""
        q = self.question
        q.add_metadata(ff_version='18.0a2')
        q.save()
        q.auto_tag()
        tags_eq(q, ['Firefox 18.0'])

    def test_auto_tagging_restraint(self):
        """Auto-tagging shouldn't tag unknown Firefox versions or OSes."""
        q = self.question
        q.add_metadata(ff_version='allyourbase', os='toaster 1.0')
        q.save()
        q.auto_tag()
        tags_eq(q, [])

    def test_tenths_version(self):
        """Test the filter that turns 1.2.3 into 1.2."""
        eq_(_tenths_version('1.2.3beta3'), '1.2')
        eq_(_tenths_version('1.2rc'), '1.2')
        eq_(_tenths_version('1.w'), '')

    def test_has_beta(self):
        """Test the _has_beta helper."""
        assert _has_beta('5.0', {'5.0b3': '2011-06-01'})
        assert not _has_beta('6.0', {'5.0b3': '2011-06-01'})
        assert not _has_beta('5.5', {'5.0b3': '2011-06-01'})
        assert _has_beta('5.7', {'5.7b1': '2011-06-01'})
        assert _has_beta('11.0', {'11.0b7': '2011-06-01'})
        assert not _has_beta('10.0', {'11.0b7': '2011-06-01'})


class QuestionTests(TestCaseBase):
    """Tests for Question model"""

    def test_save_updated(self):
        """Saving with the `update` option should update `updated`."""
        q = question(save=True)
        updated = q.updated
        q.save(update=True)
        self.assertNotEqual(updated, q.updated)

    def test_save_no_update(self):
        """Saving without the `update` option shouldn't update `updated`."""
        q = question(save=True)
        updated = q.updated
        q.save()
        eq_(updated, q.updated)

    def test_default_manager(self):
        """Assert Question's default manager is SUMO's ManagerBase.

        This is easy to get wrong when mixing in taggability.

        """
        eq_(Question._default_manager.__class__,
            kitsune.sumo.models.ManagerBase)

    def test_notification_created(self):
        """Creating a new question auto-watches it for answers."""

        u = user(save=True)
        q = question(creator=u, title='foo', content='bar', save=True)

        assert QuestionReplyEvent.is_notifying(u, q)

    def test_no_notification_on_update(self):
        """Saving an existing question does not watch it."""

        q = question(save=True)
        QuestionReplyEvent.stop_notifying(q.creator, q)
        assert not QuestionReplyEvent.is_notifying(q.creator, q)

        q.save()
        assert not QuestionReplyEvent.is_notifying(q.creator, q)

    def test_is_solved_property(self):
        a = answer(save=True)
        q = a.question
        assert not q.is_solved
        q.solution = a
        q.save()
        assert q.is_solved

    def test_recent_counts(self):
        """Verify recent_asked_count and recent unanswered count."""
        # create a question for each of past 4 days
        now = datetime.now()
        question(created=now, save=True)
        question(created=now - timedelta(hours=12), save=True, is_locked=True)
        q = question(created=now - timedelta(hours=23), save=True)
        answer(question=q, save=True)
        # 25 hours instead of 24 to avoid random test fails.
        question(created=now - timedelta(hours=25), save=True)

        # Only 3 are recent from last 72 hours, 1 has an answer.
        eq_(3, Question.recent_asked_count())
        eq_(1, Question.recent_unanswered_count())

    def test_recent_counts_with_filter(self):
        """Verify that recent_asked_count and recent_unanswered_count
        respect filters passed."""

        now = datetime.now()
        question(created=now, locale='en-US', save=True)
        q = question(created=now, locale='en-US', save=True)
        answer(question=q, save=True)

        question(created=now, locale='pt-BR', save=True)
        question(created=now, locale='pt-BR', save=True)
        q = question(created=now, locale='pt-BR', save=True)
        answer(question=q, save=True)

        # 5 asked recently, 3 are unanswered
        eq_(5, Question.recent_asked_count())
        eq_(3, Question.recent_unanswered_count())

        # check english (2 asked, 1 unanswered)
        locale_filter = Q(locale='en-US')
        eq_(2, Question.recent_asked_count(locale_filter))
        eq_(1, Question.recent_unanswered_count(locale_filter))

        # check pt-BR (3 asked, 2 unanswered)
        locale_filter = Q(locale='pt-BR')
        eq_(3, Question.recent_asked_count(locale_filter))
        eq_(2, Question.recent_unanswered_count(locale_filter))

    def test_from_url(self):
        """Verify question returned from valid URL."""
        q = question(save=True)

        eq_(q, Question.from_url('/en-US/questions/%s' % q.id))
        eq_(q, Question.from_url('/es/questions/%s' % q.id))
        eq_(q, Question.from_url('/questions/%s' % q.id))

    def test_from_url_id_only(self):
        """Verify question returned from valid URL."""
        # When requesting the id, the existence of the question isn't checked.
        eq_(123, Question.from_url('/en-US/questions/123', id_only=True))
        eq_(234, Question.from_url('/es/questions/234', id_only=True))
        eq_(345, Question.from_url('/questions/345', id_only=True))

    def test_from_invalid_url(self):
        """Verify question returned from valid URL."""
        q = question(save=True)

        eq_(None, Question.from_url('/en-US/questions/%s/edit' % q.id))
        eq_(None, Question.from_url('/en-US/kb/%s' % q.id))
        eq_(None, Question.from_url('/random/url'))
        eq_(None, Question.from_url('/en-US/questions/dashboard/metrics'))


class AddExistingTagTests(TestCaseBase):
    """Tests for the add_existing_tag helper function."""

    def setUp(self):
        super(AddExistingTagTests, self).setUp()
        self.untagged_question = question(save=True)

    def test_tags_manager(self):
        """Make sure the TaggableManager exists.

        Full testing of functionality is a matter for taggit's tests.

        """
        tags_eq(self.untagged_question, [])

    def test_add_existing_case_insensitive(self):
        """Assert add_existing_tag works case-insensitively."""
        tag(name='lemon', slug='lemon', save=True)
        add_existing_tag('LEMON', self.untagged_question.tags)
        tags_eq(self.untagged_question, [u'lemon'])

    @raises(Tag.DoesNotExist)
    def test_add_existing_no_such_tag(self):
        """Assert add_existing_tag doesn't work when the tag doesn't exist."""
        add_existing_tag('nonexistent tag', self.untagged_question.tags)


class OldQuestionsLockTest(ElasticTestCase):
    def test_lock_old_questions(self):
        last_updated = datetime.now() - timedelta(days=100)

        # created just now
        q1 = question(save=True)

        # created 200 days ago
        q2 = question(created=(datetime.now() - timedelta(days=200)),
                      updated=last_updated,
                      save=True)

        # created 200 days ago, already locked
        q3 = question(created=(datetime.now() - timedelta(days=200)),
                      is_locked=True,
                      updated=last_updated,
                      save=True)

        self.refresh()

        auto_lock_old_questions()

        # There are three questions.
        eq_(len(list(Question.objects.all())), 3)

        # q2 and q3 are now locked and updated times are the same
        locked_questions = list(Question.uncached.filter(is_locked=True))
        eq_(sorted([(q.id, q.updated.date()) for q in locked_questions]),
            [(q.id, q.updated.date()) for q in [q2, q3]])

        # q1 is still unlocked.
        locked_questions = list(Question.uncached.filter(is_locked=False))
        eq_(sorted([q.id for q in locked_questions]),
            [q1.id])


class UserActionCounts(TestCase):
    def test_user_num_questions(self):
        """Answers are counted correctly on a user."""
        u = user(save=True)

        eq_(user_num_questions(u), 0)
        q1 = question(creator=u, save=True)
        eq_(user_num_questions(u), 1)
        q2 = question(creator=u, save=True)
        eq_(user_num_questions(u), 2)
        q1.delete()
        eq_(user_num_questions(u), 1)
        q2.delete()
        eq_(user_num_questions(u), 0)

    def test_user_num_answers(self):
        u = user(save=True)
        q = question(save=True)

        eq_(user_num_answers(u), 0)
        a1 = answer(creator=u, question=q, save=True)
        eq_(user_num_answers(u), 1)
        a2 = answer(creator=u, question=q, save=True)
        eq_(user_num_answers(u), 2)
        a1.delete()
        eq_(user_num_answers(u), 1)
        a2.delete()
        eq_(user_num_answers(u), 0)

    def test_user_num_solutions(self):
        u = user(save=True)
        q1 = question(save=True)
        q2 = question(save=True)
        a1 = answer(creator=u, question=q1, save=True)
        a2 = answer(creator=u, question=q2, save=True)

        eq_(user_num_solutions(u), 0)
        q1.solution = a1
        q1.save()
        eq_(user_num_solutions(u), 1)
        q2.solution = a2
        q2.save()
        eq_(user_num_solutions(u), 2)
        q1.solution = None
        q1.save()
        eq_(user_num_solutions(u), 1)
        a2.delete()
        eq_(user_num_solutions(u), 0)


class QuestionVisitsTests(TestCase):
    """Tests for the pageview statistics gathering."""

    @mock.patch.object(googleanalytics, 'pageviews_by_question')
    def test_visit_count_from_analytics(self, pageviews_by_question):
        """Verify stored visit counts from mocked data."""
        q1 = question(save=True)
        q2 = question(save=True)
        q3 = question(save=True)

        pageviews_by_question.return_value = {
            q1.id: 42,
            q2.id: 27,
            q3.id: 1337,
            123459: 3,
        }

        QuestionVisits.reload_from_analytics()
        eq_(3, QuestionVisits.uncached.count())
        eq_(42, QuestionVisits.uncached.get(question_id=q1.id).visits)
        eq_(27, QuestionVisits.uncached.get(question_id=q2.id).visits)
        eq_(1337, QuestionVisits.uncached.get(question_id=q3.id).visits)

        # Change the data and run again to cover the update case.
        pageviews_by_question.return_value = {
            q1.id: 100,
            q2.id: 200,
            q3.id: 300,
        }
        QuestionVisits.reload_from_analytics()
        eq_(3, QuestionVisits.uncached.count())
        eq_(100, QuestionVisits.uncached.get(question_id=q1.id).visits)
        eq_(200, QuestionVisits.uncached.get(question_id=q2.id).visits)
        eq_(300, QuestionVisits.uncached.get(question_id=q3.id).visits)
