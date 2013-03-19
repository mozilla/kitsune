import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.plugins.skip import SkipTest
from nose.tools import eq_
from pyquery import PyQuery as pq
from tidings.models import Watch

from products.tests import product
from questions.events import QuestionReplyEvent, QuestionSolvedEvent
from questions.models import Question, Answer, VoteMetadata
from questions.tests import (TestCaseBase, TaggingTestCaseBase, tags_eq,
                             question, answer, questionvote)
from questions.views import UNAPPROVED_TAG, NO_TAG
from questions.cron import cache_top_contributors
from sumo.helpers import urlparams
from sumo.tests import (get, post, attrs_eq, TestCase,
                        LocalizingClient)
from sumo.urlresolvers import reverse
from topics.tests import topic
from upload.models import ImageAttachment
from users.models import RegistrationProfile
from users.tests import user, add_permission


class AnswersTemplateTestCase(TestCaseBase):
    """Test the Answers template."""
    def setUp(self):
        super(AnswersTemplateTestCase, self).setUp()

        self.client.login(username='jsocol', password='testpass')
        self.question = Question.objects.get(pk=1)
        self.answer = self.question.answers.all()[0]

    def tearDown(self):
        super(AnswersTemplateTestCase, self).tearDown()

        self.client.logout()

    def test_answer(self):
        """Posting a valid answer inserts it."""
        num_answers = self.question.answers.count()
        content = 'lorem ipsum dolor sit amet'
        response = post(self.client, 'questions.reply',
                        {'content': content},
                        args=[self.question.id])

        eq_(1, len(response.redirect_chain))
        eq_(num_answers + 1, self.question.answers.count())

        new_answer = self.question.answers.order_by('-created')[0]
        eq_(content, new_answer.content)
        # Check canonical url
        doc = pq(response.content)
        eq_('/questions/1', doc('link[rel="canonical"]')[0].attrib['href'])

    def test_answer_upload(self):
        """Posting answer attaches an existing uploaded image to the answer."""

        f = open('apps/upload/tests/media/test.jpg')
        post(self.client, 'upload.up_image_async', {'image': f},
             args=['questions.Question', self.question.id])
        f.close()

        content = 'lorem ipsum dolor sit amet'
        response = post(self.client, 'questions.reply',
                        {'content': content},
                        args=[self.question.id])
        eq_(200, response.status_code)

        new_answer = self.question.answers.order_by('-created')[0]
        eq_(1, new_answer.images.count())
        image = new_answer.images.all()[0]
        name = '098f6b.png'
        message = 'File name "%s" does not contain "%s"' % (
            image.file.name, name)
        assert name in image.file.name, message
        eq_('jsocol', image.creator.username)

        # Clean up
        ImageAttachment.objects.all().delete()

    def test_empty_answer(self):
        """Posting an empty answer shows error."""
        response = post(self.client, 'questions.reply', {'content': ''},
                        args=[self.question.id])

        doc = pq(response.content)
        error_msg = doc('ul.errorlist li a')[0]
        eq_(error_msg.text, 'Please provide content.')

    def test_short_answer(self):
        """Posting a short answer shows error."""
        response = post(self.client, 'questions.reply', {'content': 'lor'},
                        args=[self.question.id])

        doc = pq(response.content)
        error_msg = doc('ul.errorlist li a')[0]
        eq_(error_msg.text, 'Your content is too short (3 characters). ' +
                            'It must be at least 5 characters.')

    def test_long_answer(self):
        """Post a long answer shows error."""

        # Set up content length to 10,001 characters
        content = ''
        for i in range(1000):
            content += '1234567890'
        content += '1'

        response = post(self.client, 'questions.reply', {'content': content},
                        args=[self.question.id])

        doc = pq(response.content)
        error_msg = doc('ul.errorlist li a')[0]
        eq_(error_msg.text, 'Please keep the length of your content to ' +
                            '10,000 characters or less. It is currently ' +
                            '10,001 characters.')

    def test_solve_unsolve(self):
        """Test accepting a solution and undoing."""
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(0, len(doc('div.solution')))

        ans = self.question.answers.all()[0]
        # Solve and verify
        response = post(self.client, 'questions.solve',
                        args=[self.question.id, ans.id])
        doc = pq(response.content)
        eq_(1, len(doc('div.solution')))
        div = doc('h3.is-solution')[0].getparent().getparent()
        eq_('answer-%s' % ans.id, div.attrib['id'])
        q = Question.uncached.get(pk=self.question.id)
        eq_(q.solution, ans)
        # Unsolve and verify
        response = post(self.client, 'questions.unsolve',
                        args=[self.question.id, ans.id])
        q = Question.uncached.get(pk=self.question.id)
        eq_(q.solution, None)

    def test_only_owner_or_admin_can_solve_unsolve(self):
        """Make sure non-owner/non-admin can't solve/unsolve."""
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(1, len(doc('input[name="solution"]')))

        self.client.logout()
        self.client.login(username='pcraciunoiu', password='testpass')
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(0, len(doc('input[name="solution"]')))

        ans = self.question.answers.all()[0]
        # Try to solve
        response = post(self.client, 'questions.solve',
                        args=[self.question.id, ans.id])
        eq_(403, response.status_code)
        # Try to unsolve
        response = post(self.client, 'questions.unsolve',
                        args=[self.question.id, ans.id])
        eq_(403, response.status_code)

    def test_solve_unsolve_with_perm(self):
        """Test marking solve/unsolve with 'change_solution' permission."""
        u = user(save=True)
        add_permission(u, Question, 'change_solution')
        self.client.login(username=u.username, password='testpass')
        ans = self.question.answers.all()[0]
        # Solve and verify
        post(self.client, 'questions.solve',
             args=[self.question.id, ans.id])
        q = Question.uncached.get(pk=self.question.id)
        eq_(q.solution, ans)
        # Unsolve and verify
        post(self.client, 'questions.unsolve',
             args=[self.question.id, ans.id])
        q = Question.uncached.get(pk=self.question.id)
        eq_(q.solution, None)

    def test_question_vote_GET(self):
        """Attempting to vote with HTTP GET returns a 405."""
        response = get(self.client, 'questions.vote',
                       args=[self.question.id])
        eq_(405, response.status_code)

    def common_vote(self):
        """Helper method for question vote tests."""
        # Check that there are no votes and vote form renders
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        assert '0\n' in doc('.have-problem')[0].text
        eq_(1, len(doc('div.me-too form')))

        # Vote
        ua = 'Mozilla/5.0 (DjangoTestClient)'
        self.client.post(reverse('questions.vote', args=[self.question.id]),
                         {}, HTTP_USER_AGENT=ua)

        # Check that there is 1 vote and vote form doesn't render
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        assert '1\n' in doc('.have-problem')[0].text
        eq_(0, len(doc('div.me-too form')))
        # Verify user agent
        vote_meta = VoteMetadata.objects.all()[0]
        eq_('ua', vote_meta.key)
        eq_(ua, vote_meta.value)

        # Voting again (same user) should not increment vote count
        post(self.client, 'questions.vote', args=[self.question.id])
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        assert '1\n' in doc('.have-problem')[0].text

    def test_question_authenticated_vote(self):
        """Authenticated user vote."""
        # Common vote test
        self.common_vote()

    def test_question_anonymous_vote(self):
        """Anonymous user vote."""
        # Log out
        self.client.logout()

        # Common vote test
        self.common_vote()

    def common_answer_vote(self):
        """Helper method for answer vote tests."""
        # Check that there are no votes and vote form renders
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(1, len(doc('form.helpful input[name="helpful"]')))

        # Vote
        ua = 'Mozilla/5.0 (DjangoTestClient)'
        self.client.post(reverse('questions.answer_vote',
                                 args=[self.question.id, self.answer.id]),
                         {'helpful': 'y'}, HTTP_USER_AGENT=ua)

        # Check that there is 1 vote and vote form doesn't render
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)

        eq_(1, len(doc('#answer-1 h3.is-helpful')))
        eq_(0, len(doc('form.helpful input[name="helpful"]')))
        # Verify user agent
        vote_meta = VoteMetadata.objects.all()[0]
        eq_('ua', vote_meta.key)
        eq_(ua, vote_meta.value)

    def test_answer_authenticated_vote(self):
        """Authenticated user answer vote."""
        # log in as rrosario (didn't ask or answer question)
        self.client.logout()
        self.client.login(username='rrosario', password='testpass')

        # Common vote test
        self.common_answer_vote()

    def test_answer_anonymous_vote(self):
        """Anonymous user answer vote."""
        # Log out
        self.client.logout()

        # Common vote test
        self.common_answer_vote()

    def test_can_vote_on_asker_reply(self):
        """An answer posted by the asker can be voted on."""
        self.client.logout()
        # Post a new answer by the asker => two votable answers
        q = self.question
        Answer.objects.create(question=q, creator=q.creator, content='test')
        response = get(self.client, 'questions.answers', args=[q.id])
        doc = pq(response.content)
        eq_(2, len(doc('form.helpful input[name="helpful"]')))

    def test_asker_can_vote(self):
        """The asker can vote Not/Helpful."""
        self.client.login(username=self.question.creator.username,
                          password='testpass')
        self.common_answer_vote()

    def test_can_solve_with_answer_by_asker(self):
        """An answer posted by the asker can be the solution."""
        self.client.login(username=self.question.creator.username,
                          password='testpass')
        # Post a new answer by the asker => two solvable answers
        q = self.question
        Answer.objects.create(question=q, creator=q.creator, content='test')
        response = get(self.client, 'questions.answers', args=[q.id])
        doc = pq(response.content)
        eq_(2, len(doc('form.solution input[name="solution"]')))

    def test_delete_question_without_permissions(self):
        """Deleting a question without permissions is a 403."""
        self.client.login(username='tagger', password='testpass')
        response = get(self.client, 'questions.delete',
                       args=[self.question.id])
        eq_(403, response.status_code)
        response = post(self.client, 'questions.delete',
                        args=[self.question.id])
        eq_(403, response.status_code)

    def test_delete_question_logged_out(self):
        """Deleting a question while logged out redirects to login."""
        self.client.logout()
        response = get(self.client, 'questions.delete',
                       args=[self.question.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/%s%s?next=/en-US/questions/1/delete' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL), redirect[0])

        response = post(self.client, 'questions.delete',
                        args=[self.question.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/%s%s?next=/en-US/questions/1/delete' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL), redirect[0])

    def test_delete_question_with_permissions(self):
        """Deleting a question with permissions."""
        self.client.login(username='admin', password='testpass')
        response = get(self.client, 'questions.delete',
                       args=[self.question.id])
        eq_(200, response.status_code)

        response = post(self.client, 'questions.delete',
                        args=[self.question.id])
        eq_(0, Question.objects.filter(pk=self.question.id).count())

    def test_delete_answer_without_permissions(self):
        """Deleting an answer without permissions sends 403."""
        self.client.login(username='tagger', password='testpass')
        ans = self.question.last_answer
        response = get(self.client, 'questions.delete_answer',
                       args=[self.question.id, ans.id])
        eq_(403, response.status_code)

        response = post(self.client, 'questions.delete_answer',
                        args=[self.question.id, ans.id])
        eq_(403, response.status_code)

    def test_delete_answer_logged_out(self):
        """Deleting an answer while logged out redirects to login."""
        self.client.logout()
        ans = self.question.last_answer
        response = get(self.client, 'questions.delete_answer',
                       args=[self.question.id, ans.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/%s%s?next=/en-US/questions/1/delete/1' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL), redirect[0])

        response = post(self.client, 'questions.delete_answer',
                        args=[self.question.id, ans.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/%s%s?next=/en-US/questions/1/delete/1' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL), redirect[0])

    def test_delete_answer_with_permissions(self):
        """Deleting an answer with permissions."""
        ans = self.question.last_answer
        self.client.login(username='admin', password='testpass')
        response = get(self.client, 'questions.delete_answer',
                       args=[self.question.id, ans.id])
        eq_(200, response.status_code)

        response = post(self.client, 'questions.delete_answer',
                        args=[self.question.id, ans.id])
        eq_(0, Answer.objects.filter(pk=self.question.id).count())

    def test_edit_answer_without_permission(self):
        """Editing an answer without permissions returns a 403.

        The edit link shouldn't show up on the Answers page."""
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(0, len(doc('ol.answers li.edit')))

        answer = self.question.last_answer
        response = get(self.client, 'questions.edit_answer',
                       args=[self.question.id, answer.id])
        eq_(403, response.status_code)

        content = 'New content for answer'
        response = post(self.client, 'questions.edit_answer',
                        {'content': content},
                        args=[self.question.id, answer.id])
        eq_(403, response.status_code)

    def test_edit_answer_with_permissions(self):
        """Editing an answer with permissions.

        The edit link should show up on the Answers page."""
        self.client.login(username='admin', password='testpass')

        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(2, len(doc('li.edit')))

        answer = self.question.last_answer
        response = get(self.client, 'questions.edit_answer',
                       args=[self.question.id, answer.id])
        eq_(200, response.status_code)

        content = 'New content for answer'
        response = post(self.client, 'questions.edit_answer',
                        {'content': content},
                        args=[self.question.id, answer.id])
        eq_(content, Answer.objects.get(pk=answer.id).content)

    def test_answer_creator_can_edit(self):
        """The creator of an answer can edit his/her answer."""
        self.client.login(username='rrosario', password='testpass')

        # Initially there should be no edit links
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_(0, len(doc('ol.answers li.edit')))

        # Add an answer and verify the edit link shows up
        content = 'lorem ipsum dolor sit amet'
        response = post(self.client, 'questions.reply',
                        {'content': content},
                        args=[self.question.id])
        doc = pq(response.content)
        eq_(1, len(doc('li.edit')))
        new_answer = self.question.answers.order_by('-created')[0]
        eq_(1, len(doc('#answer-%s + div li.edit' % new_answer.id)))

        # Make sure it can be edited
        content = 'New content for answer'
        response = post(self.client, 'questions.edit_answer',
                        {'content': content},
                        args=[self.question.id, new_answer.id])
        eq_(200, response.status_code)

        # Now lock it and make sure it can't be edited
        self.question.is_locked = True
        self.question.save()
        response = post(self.client, 'questions.edit_answer',
                        {'content': content},
                        args=[self.question.id, new_answer.id])
        eq_(403, response.status_code)

    def test_lock_question_without_permissions(self):
        """Trying to lock a question without permission is a 403."""
        self.client.login(username='tagger', password='testpass')
        q = self.question
        response = post(self.client, 'questions.lock', args=[q.id])
        eq_(403, response.status_code)

    def test_lock_question_logged_out(self):
        """Trying to lock a question while logged out redirects to login."""
        self.client.logout()
        q = self.question
        response = post(self.client, 'questions.lock', args=[q.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/%s%s?next=/en-US/questions/1/lock' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL), redirect[0])

    def test_lock_question_with_permissions_GET(self):
        """Trying to lock a question via HTTP GET."""
        response = get(self.client, 'questions.lock', args=[self.question.id])
        eq_(405, response.status_code)

    def test_lock_question_with_permissions_POST(self):
        """Locking questions with permissions via HTTP POST."""
        self.client.login(username='admin', password='testpass')
        q = self.question
        response = post(self.client, 'questions.lock', args=[q.id])
        eq_(200, response.status_code)
        eq_(True, Question.objects.get(pk=q.pk).is_locked)
        assert 'This thread was closed.' in response.content

        # now unlock it
        response = post(self.client, 'questions.lock', args=[q.id])
        eq_(200, response.status_code)
        eq_(False, Question.objects.get(pk=q.pk).is_locked)

    def test_reply_to_locked_question_403(self):
        """Locked questions can't be answered."""
        q = self.question
        q.is_locked = True
        q.save()
        response = post(self.client, 'questions.reply',
                        {'content': 'just testing'}, args=[q.id])
        eq_(403, response.status_code)

    def test_vote_locked_question_403(self):
        """Locked questions can't be voted on."""
        q = self.question
        q.is_locked = True
        q.save()
        self.client.login(username='rrosario', password='testpass')
        response = post(self.client, 'questions.vote', args=[q.id])
        eq_(403, response.status_code)

    def test_vote_answer_to_locked_question_403(self):
        """Answers to locked questions can't be voted on."""
        q = self.question
        q.is_locked = True
        q.save()
        self.client.login(username='rrosario', password='testpass')
        response = post(self.client, 'questions.answer_vote',
                        {'helpful': 'y'}, args=[q.id, self.answer.id])
        eq_(403, response.status_code)

    def test_watch_GET_405(self):
        """Watch replies with HTTP GET results in 405."""
        self.client.login(username='rrosario', password='testpass')
        response = get(self.client, 'questions.watch',
                       args=[self.question.id])
        eq_(405, response.status_code)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_solution(self, get_current):
        """Watch a question for solution."""
        self.client.logout()
        get_current.return_value.domain = 'testserver'

        post(self.client, 'questions.watch',
             {'email': 'some@bo.dy'},
             args=[self.question.id])
        assert QuestionSolvedEvent.is_notifying('some@bo.dy', self.question), (
               'Watch was not created')

        attrs_eq(mail.outbox[0], to=['some@bo.dy'],
                 subject='Please confirm your email address')
        assert 'questions/confirm/' in mail.outbox[0].body
        assert 'Solution found' in mail.outbox[0].body

        # Now activate the watch.
        w = Watch.objects.get()
        get(self.client, 'questions.activate_watch', args=[w.id, w.secret])
        assert Watch.objects.get().is_active

    def test_watch_solution_and_replies(self):
        """User subscribes to solution and replies: page doesn't break"""
        self.client.login(username='rrosario', password='testpass')
        user = User.objects.get(username='rrosario')
        QuestionReplyEvent.notify(user, self.question)
        QuestionSolvedEvent.notify(user, self.question)
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        eq_(200, response.status_code)

    def test_preview_answer(self):
        """Preview an answer."""
        num_answers = self.question.answers.count()
        content = 'Awesome answer.'
        response = post(self.client, 'questions.reply',
                        {'content': content, 'preview': 'any string'},
                        args=[self.question.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(content, doc('#answer-preview div.main-content').text())
        eq_(num_answers, self.question.answers.count())

    def test_preview_answer_as_admin(self):
        """Preview an answer as admin and verify response is 200."""
        self.client.login(username='admin', password='testpass')
        content = 'Awesome answer.'
        response = post(self.client, 'questions.reply',
                        {'content': content, 'preview': 'any string'},
                        args=[self.question.id])
        eq_(200, response.status_code)

    def test_links_nofollow(self):
        """Links posted in questions and answers should have rel=nofollow."""
        q = self.question
        q.content = 'lorem http://ipsum.com'
        q.save()
        a = self.answer
        a.content = 'testing http://example.com'
        a.save()
        response = get(self.client, 'questions.answers',
                       args=[self.question.id])
        doc = pq(response.content)
        eq_('nofollow', doc('.question .main-content a')[0].attrib['rel'])
        eq_('nofollow', doc('.answer .main-content a')[0].attrib['rel'])

    def test_robots_noindex(self):
        """Verify noindex on unanswered questions over 30 days old."""
        q = question(save=True)

        # A brand new questions shouldn't be noindex'd...
        response = get(self.client, 'questions.answers', args=[q.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc('meta[name=robots]')))

        # But a 31 day old question should be noindexed...
        q.created = datetime.now() - timedelta(days=31)
        q.save()
        response = get(self.client, 'questions.answers', args=[q.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('meta[name=robots]')))

        # Except if it has answers.
        answer(question=q, save=True)
        response = get(self.client, 'questions.answers', args=[q.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc('meta[name=robots]')))

class TaggedQuestionsTestCase(TaggingTestCaseBase):
    """Questions/answers template tests that require tagged questions."""

    def setUp(self):
        super(TaggedQuestionsTestCase, self).setUp()

        q = Question.objects.get(pk=1)
        q.tags.add('green')

    def test_related_list(self):
        """Test that related Questions appear in the list."""

        raise SkipTest

        question = Question.objects.get(pk=1)
        response = get(self.client, 'questions.answers',
                       args=[question.id])
        doc = pq(response.content)
        eq_(1, len(doc('ul.related li')))


class TaggingViewTestsAsTagger(TaggingTestCaseBase):
    """Tests for views that add and remove tags, logged in as someone who can
    add and remove but not create tags

    Also hits the tag-related parts of the answer template.

    """
    def setUp(self):
        super(TaggingViewTestsAsTagger, self).setUp()

        # Assign tag_question permission to the "tagger" user.
        # Would be nice to have a natural key for doing this via a fixture.
        self._can_tag = Permission.objects.get_by_natural_key('tag_question',
                                                              'questions',
                                                              'question')
        self._user = User.objects.get(username='tagger')
        self._user.user_permissions.add(self._can_tag)

        self.client.login(username='tagger', password='testpass')

    def tearDown(self):
        self.client.logout()
        self._user.user_permissions.remove(self._can_tag)
        super(TaggingViewTestsAsTagger, self).tearDown()

    # add_tag view:

    def test_add_tag_get_method(self):
        """Assert GETting the add_tag view redirects to the answers page."""
        response = self.client.get(_add_tag_url())
        url = 'http://testserver%s' % reverse('questions.answers',
                                              kwargs={'question_id': 1},
                                              force_locale=True)
        self.assertRedirects(response, url)

    def test_add_nonexistent_tag(self):
        """Assert adding a nonexistent tag sychronously shows an error."""
        response = self.client.post(_add_tag_url(),
                                    data={'tag-name': 'nonexistent tag'})
        self.assertContains(response, UNAPPROVED_TAG)

    def test_add_existent_tag(self):
        """Test adding a tag, case insensitivity, and space stripping."""
        response = self.client.post(_add_tag_url(),
                                    data={'tag-name': ' PURplepurplepurple '},
                                    follow=True)
        self.assertContains(response, 'purplepurplepurple')

    def test_add_no_tag(self):
        """Make sure adding a blank tag shows an error message."""
        response = self.client.post(_add_tag_url(),
                                    data={'tag-name': ''})
        self.assertContains(response, NO_TAG)

    # add_tag_async view:

    def test_add_async_nonexistent_tag(self):
        """Assert adding an nonexistent tag yields an AJAX error."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': 'nonexistent tag'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, UNAPPROVED_TAG, status_code=400)

    def test_add_async_existent_tag(self):
        """Assert adding an unapplied tag yields an AJAX error."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': ' PURplepurplepurple '},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'canonicalName')
        eq_([t.name for t in Question.objects.get(pk=1).tags.all()],
            ['purplepurplepurple'])  # Test the backend since we don't have a
                                     # newly rendered page to rely on.

    def test_add_async_no_tag(self):
        """Assert adding an empty tag asynchronously yields an AJAX error."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': ''},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, NO_TAG, status_code=400)

    # remove_tag view:

    def test_remove_applied_tag(self):
        """Assert removing an applied tag succeeds."""
        response = self.client.post(_remove_tag_url(),
                                    data={'remove-tag-colorless': 'dummy'})
        self._assert_redirects_to_question_2(response)
        eq_([t.name for t in Question.objects.get(pk=2).tags.all()], ['green'])

    def test_remove_unapplied_tag(self):
        """Test removing an unapplied tag fails silently."""
        response = self.client.post(_remove_tag_url(),
                                    data={'remove-tag-lemon': 'dummy'})
        self._assert_redirects_to_question_2(response)

    def test_remove_no_tag(self):
        """Make sure removing with no params provided redirects harmlessly."""
        response = self.client.post(_remove_tag_url(),
                                    data={})
        self._assert_redirects_to_question_2(response)

    def _assert_redirects_to_question_2(self, response):
        url = 'http://testserver%s' % reverse('questions.answers',
                                              kwargs={'question_id': 2},
                                              force_locale=True)
        self.assertRedirects(response, url)

    # remove_tag_async view:

    def test_remove_async_applied_tag(self):
        """Assert taking a tag off a question works."""
        response = self.client.post(_remove_async_tag_url(),
                                    data={'name': 'colorless'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)
        eq_([t.name for t in Question.objects.get(pk=2).tags.all()], ['green'])

    def test_remove_async_unapplied_tag(self):
        """Assert trying to remove a tag that isn't there succeeds."""
        response = self.client.post(_remove_async_tag_url(),
                                    data={'name': 'lemon'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

    def test_remove_async_no_tag(self):
        """Assert calling the remove handler with no param fails."""
        response = self.client.post(_remove_async_tag_url(),
                                    data={},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, NO_TAG, status_code=400)


class TaggingViewTestsAsAdmin(TaggingTestCaseBase):
    """Tests for views that create new tags, logged in as someone who can"""

    def setUp(self):
        super(TaggingViewTestsAsAdmin, self).setUp()
        self.client.login(username='admin', password='testpass')

    def tearDown(self):
        self.client.logout()
        super(TaggingViewTestsAsAdmin, self).tearDown()

    def test_add_new_tag(self):
        """Assert adding a nonexistent tag sychronously creates & adds it."""
        self.client.post(_add_tag_url(), data={'tag-name': 'nonexistent tag'})
        tags_eq(Question.objects.get(pk=1), ['nonexistent tag'])

    def test_add_async_new_tag(self):
        """Assert adding an nonexistent tag creates & adds it."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': 'nonexistent tag'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)
        tags_eq(Question.objects.get(pk=1), ['nonexistent tag'])

    def test_add_new_case_insensitive(self):
        """Adding a tag differing only in case from existing ones shouldn't
        create a new tag."""
        self.client.post(_add_async_tag_url(), data={'tag-name': 'RED'},
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        tags_eq(Question.objects.get(pk=1), ['red'])

    def test_add_new_canonicalizes(self):
        """Adding a new tag as an admin should still canonicalize case."""
        response = self.client.post(_add_async_tag_url(),
                                    data={'tag-name': 'RED'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(json.loads(response.content)['canonicalName'], 'red')


def _add_tag_url():
    """Return the URL to add_tag for question 1, an untagged question."""
    return reverse('questions.add_tag', kwargs={'question_id': 1})


def _add_async_tag_url():
    """Return the URL to add_tag_async for question 1, an untagged question."""
    return reverse('questions.add_tag_async', kwargs={'question_id': 1})


def _remove_tag_url():
    """Return  URL to remove_tag for question 2, tagged {colorless, green}."""
    return reverse('questions.remove_tag', kwargs={'question_id': 2})


def _remove_async_tag_url():
    """Return URL to remove_tag_async on q. 2, tagged {colorless, green}."""
    return reverse('questions.remove_tag_async', kwargs={'question_id': 2})


class QuestionsTemplateTestCase(TestCaseBase):

    def test_all_filter_highlight(self):
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_('active', doc('ul.show li')[0].attrib['class'])
        eq_('question-1', doc('.questions > section')[0].attrib['id'])

    def test_no_reply_filter(self):
        url_ = urlparams(reverse('questions.questions'),
                         filter='no-replies')
        q = question(save=True)
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_('active', doc('ul.show li')[-1].attrib['class'])
        eq_('question-%s' % q.id, doc('.questions > section')[0].attrib['id'])
        eq_('/questions?filter=no-replies',
            doc('link[rel="canonical"]')[0].attrib['href'])

    def test_solved_filter(self):
        # initially there should be no solved answers
        url_ = urlparams(reverse('questions.questions'),
                         filter='solved')
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_('active', doc('ul.show li')[2].attrib['class'])
        eq_(0, len(doc('ol.questions li')))
        eq_('/questions?filter=solved',
            doc('link[rel="canonical"]')[0].attrib['href'])

        # solve one question then verify that it shows up
        answer = Answer.objects.all()[0]
        answer.question.solution = answer
        answer.question.save()
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_(1, len(doc('.questions > section')))
        eq_('question-%s' % answer.question.id,
            doc('.questions > section')[0].attrib['id'])

    def test_unsolved_filter(self):
        # initially there should be 2 unsolved answers
        url_ = urlparams(reverse('questions.questions'),
                         filter='unsolved')
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_('active', doc('ul.show li')[1].attrib['class'])
        eq_(2, len(doc('.questions > section')))

        # solve one question then verify that it doesn't show up
        answer = Answer.objects.all()[0]
        answer.question.solution = answer
        answer.question.save()
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_(1, len(doc('.questions > section')))
        eq_(0, len(doc('.questions #question-%s' % answer.question.id)))
        eq_('/questions?filter=unsolved',
            doc('link[rel="canonical"]')[0].attrib['href'])

    def _my_contributions_test_helper(self, username, expected_qty):
        url_ = urlparams(reverse('questions.questions'),
                         filter='my-contributions')
        self.client.login(username=username, password="testpass")
        response = self.client.get(url_)
        doc = pq(response.content)
        eq_('active', doc('ul.show li')[-1].attrib['class'])
        eq_(expected_qty, len(doc('.questions > section')))
        eq_('/questions?filter=my-contributions',
            doc('link[rel="canonical"]')[0].attrib['href'])

    def test_my_contributions_filter(self):
        # jsocol should have 2 questions in his contributions
        self._my_contributions_test_helper('jsocol', 2)

        # pcraciunoiu should have 2 questions in his contributions'
        self._my_contributions_test_helper('pcraciunoiu', 2)

        # rrosario should have 0 questions in his contributions
        self._my_contributions_test_helper('rrosario', 0)

    def test_contributed_badge(self):
        # pcraciunoiu should have a contributor badge on question 1 but not 2
        self.client.login(username='pcraciunoiu', password="testpass")
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(1, len(doc('#question-1 .thread-contributed.highlighted')))
        eq_(0, len(doc('#question-2 .thread-contributed.highlighted')))

    def test_sort(self):
        # This test fails occasionally and needs to be rewritten. So for now
        # we're skipping it!
        raise SkipTest

        # TODO: Rewrite this test because it's like the test that
        # cried wolf and I ignore it.
        default = reverse('questions.questions')
        sorted = urlparams(default, sort='requested')

        q = Question.objects.get(pk=2)
        answer(question=q, save=True)

        response = self.client.get(default)
        doc = pq(response.content)
        eq_('question-1', doc('ol.questions li')[0].attrib['id'])

        q.num_votes_past_week = 7
        q.save()

        response = self.client.get(sorted)
        doc = pq(response.content)
        eq_('question-2', doc('ol.questions li')[0].attrib['id'])
        eq_('/questions?sort=requested',
            doc('link[rel="canonical"]')[0].attrib['href'])

    def test_top_contributors(self):
        # There should be no top contributors since there are no solutions.
        cache_top_contributors()
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(0, len(doc('#top-contributors ol li')))

        # Solve a question and verify we now have a top conributor.
        answer = Answer.objects.all()[0]
        answer.created = datetime.now()
        answer.save()
        answer.question.solution = answer
        answer.question.save()
        cache_top_contributors()
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        lis = doc('#top-contributors ol li')
        eq_(1, len(lis))
        eq_('pcraciunoiu', lis[0].text)

        # Make answer 8 days old. There should no be top contributors.
        answer.created = datetime.now() - timedelta(days=8)
        answer.save()
        cache_top_contributors()
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(0, len(doc('#top-contributors ol li')))

    def test_tagged(self):
        self.client.login(username='admin', password="testpass")
        tagname = 'mobile'
        tagged = urlparams(reverse('questions.questions'), tagged=tagname)

        # First there should be no questions tagged 'mobile'
        response = self.client.get(tagged)
        doc = pq(response.content)
        eq_(0, len(doc('ol.questions > li')))

        # Tag a question 'mobile'
        question = Question.objects.get(pk=2)
        response = post(self.client, 'questions.add_tag',
                        {'tag-name': tagname},
                        args=[question.id])
        eq_(200, response.status_code)

        # Add an answer
        answer(question=question, save=True)

        # Now there should be 1 question tagged 'mobile'
        response = self.client.get(tagged)
        doc = pq(response.content)
        eq_(1, len(doc('.questions > section')))
        eq_('/questions?tagged=mobile',
            doc('link[rel="canonical"]')[0].attrib['href'])

    def test_product_filter(self):
        p1 = product(save=True)
        p2 = product(save=True)
        p3 = product(save=True)

        q1 = question(save=True)
        q2 = question(save=True)
        q2.products.add(p1)
        q2.save()
        q3 = question(save=True)
        q3.products.add(p1, p2)
        q3.save()

        url = reverse('questions.questions')

        def check(filter, expected):
            response = self.client.get(urlparams(url, **filter))
            doc = pq(response.content)
            # Make sure all questions are there.

            # This won't work, because the test case base adds more tests than
            # we expect in it's setUp(). TODO: Fix that.
            #eq_(len(expected), len(doc('.questions > section')))

            for q in expected:
                eq_(1, len(doc('.questions > section[id=question-%s]' % q.id)))

        # No filtering -> All questions.
        check({}, [q1, q2, q3])
        # Filter on p1 -> only q2 and q3
        check({'product': p1.slug}, [q2, q3])
        # Filter on p2 -> only q3
        check({'product': p2.slug}, [q3])
        # Filter on p3 -> No results
        check({'product': p3.slug}, [])

    def test_topic_filter(self):
        t1 = topic(save=True)
        t2 = topic(save=True)
        t3 = topic(save=True)

        q1 = question(save=True)
        q2 = question(save=True)
        q2.topics.add(t1)
        q2.save()
        q3 = question(save=True)
        q3.topics.add(t1, t2)
        q3.save()

        url = reverse('questions.questions')

        def check(filter, expected):
            response = self.client.get(urlparams(url, **filter))
            doc = pq(response.content)
            # Make sure all questions are there.

            # This won't work, because the test case base adds more tests than
            # we expect in it's setUp(). TODO: Fix that.
            #eq_(len(expected), len(doc('.questions > section')))

            for q in expected:
                eq_(1, len(doc('.questions > section[id=question-%s]' % q.id)))

        # No filtering -> All questions.
        check({}, [q1, q2, q3])
        # Filter on p1 -> only q2 and q3
        check({'topic': t1.slug}, [q2, q3])
        # Filter on p2 -> only q3
        check({'topic': t2.slug}, [q3])
        # Filter on p3 -> No results
        check({'topic': t3.slug}, [])

    def test_product_query_params(self):
        """Test that the urls generated include the right query parameters."""

        p1 = product(save=True)
        url = urlparams(reverse('questions.questions'), product=p1.slug)
        resp = self.client.get(url)
        doc = pq(resp.content)
        assert ('product=%s' % p1.slug) in doc('.sort-by >li > a')[0].attrib['href']
        assert ('product=%s' % p1.slug) in doc('.sort-by >li > a')[1].attrib['href']

        product_input = doc('#tag-filter input[type=hidden][name=product]')
        eq_(1, len(product_input))
        eq_(p1.slug, product_input[0].attrib['value'])


class QuestionsTemplateTestCaseNoFixtures(TestCase):
    client_class = LocalizingClient

    def test_locked_questions_dont_appear(self):
        """Locked questions are not listed on the no-replies list."""
        question(save=True)
        question(save=True)
        question(is_locked=True, save=True)

        url = reverse('questions.questions')
        url = urlparams(url, filter='no-replies')
        response = self.client.get(url)
        doc = pq(response.content)
        eq_(2, len(doc('article.questions > section')))

    def test_order_by_votes(self):
        #set up 3 questions with same number of votes in last week
        #but different # of total votes
        q1 = question(title="QUEST_A", num_votes_past_week=1, save=True)
        q2 = question(title="QUEST_B", num_votes_past_week=1, save=True)
        q3 = question(title="QUEST_C", num_votes_past_week=1, save=True)

        questionvote(question=q1, save=True)

        questionvote(question=q2, save=True)
        questionvote(question=q2,
                created=datetime(2012, 7, 9, 9, 0, 0),
                save=True)
        questionvote(question=q2,
                created=datetime(2012, 7, 9, 9, 0, 0),
                save=True)

        questionvote(question=q3, save=True)
        questionvote(question=q3,
                created=datetime(2012, 7, 9, 9, 0, 0),
                save=True)

        url = urlparams(
            reverse('questions.questions'),
            sort='requested')

        response = self.client.get(url, follow=True)
        eq_(True, response.content.find("QUEST_B") <
                response.content.find("QUEST_C") <
                response.content.find("QUEST_A"))


class QuestionEditingTests(TestCaseBase):
    """Tests for the question-editing view and templates"""

    def setUp(self):
        super(QuestionEditingTests, self).setUp()
        self.client.login(username='admin', password='testpass')

    def tearDown(self):
        self.client.logout()
        super(QuestionEditingTests, self).tearDown()

    def test_extra_fields(self):
        """The edit-question form should show appropriate metadata fields."""
        question_id = 1
        response = get(self.client, 'questions.edit_question',
                       kwargs={'question_id': question_id})
        eq_(response.status_code, 200)

        # Make sure each extra metadata field is in the form:
        doc = pq(response.content)
        q = Question.objects.get(pk=question_id)
        extra_fields = q.product.get('extra_fields', []) + \
                       q.category.get('extra_fields', [])
        for field in extra_fields:
            assert doc('input[name=%s]' % field) or \
                   doc('textarea[name=%s]' % field), \
                   "The %s field is missing from the edit page.""" % field

    def test_no_extra_fields(self):
        """The edit-question form shouldn't show inappropriate metadata."""
        response = get(self.client, 'questions.edit_question',
                       kwargs={'question_id': 2})
        eq_(response.status_code, 200)

        # Take the "os" field as representative. Make sure it doesn't show up:
        doc = pq(response.content)
        assert not doc('input[name=os]')

    def test_post(self):
        """Posting a valid edit form should save the question."""
        question_id = 1
        response = post(self.client, 'questions.edit_question',
                       {'title': 'New title',
                        'content': 'New content',
                        'ff_version': 'New version'},
                       kwargs={'question_id': question_id})

        # Make sure the form redirects and thus appears to succeed:
        url = 'http://testserver%s' % reverse('questions.answers',
                                           kwargs={'question_id': question_id},
                                           force_locale=True)
        self.assertRedirects(response, url)

        # Make sure the static fields, the metadata, and the updated_by field
        # changed:
        q = Question.objects.get(pk=question_id)
        eq_(q.title, 'New title')
        eq_(q.content, 'New content')
        eq_(q.metadata['ff_version'], 'New version')
        eq_(q.updated_by, User.objects.get(username='admin'))


class AAQTemplateTestCase(TestCaseBase):
    """Test the AAQ template."""
    data = {'title': 'A test question',
            'content': 'I have this question that I hope...',
            'sites_affected': 'http://example.com',
            'ff_version': '3.6.6',
            'os': 'Intel Mac OS X 10.6',
            'plugins': '* Shockwave Flash 10.1 r53',
            'useragent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X '
                         '10.6; en-US; rv:1.9.2.6) Gecko/20100625 '
                         'Firefox/3.6.6'}

    def setUp(self):
        super(AAQTemplateTestCase, self).setUp()
        self.client.login(username='jsocol', password='testpass')

    def tearDown(self):
        super(AAQTemplateTestCase, self).tearDown()
        self.client.logout()

    def _post_new_question(self, locale=None):
        """Post a new question and return the response."""
        topic(title='Fix problems', slug='fix-problems', save=True)
        product(title='Firefox', slug='firefox', save=True)
        extra = {}
        if locale is not None:
            extra['locale'] = locale
        url = urlparams(
            reverse('questions.aaq_step5', args=['desktop', 'fix-problems'],
                    **extra),
            search='A test question')
        return self.client.post(url, self.data, follow=True)

    def test_full_workflow(self):
        response = self._post_new_question()
        eq_(200, response.status_code)
        assert 'Done!' in pq(response.content)('ul.user-messages li').text()

        # Verify question is in db now
        question = Question.objects.filter(title='A test question')[0]

        # Make sure question is in questions list
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(1, len(doc('#question-%s' % question.id)))
        # And no email was sent
        eq_(0, len(mail.outbox))

        # Verify product and topic assigned to question.
        topics = question.topics.all()
        eq_(1, len(topics))
        eq_('fix-problems', topics[0].slug)
        products = question.products.all()
        eq_(1, len(products))
        eq_('firefox', products[0].slug)

    def test_localized_creation(self):
        response = self._post_new_question(locale='de')
        eq_(200, response.status_code)
        assert 'Done!' in pq(response.content)('ul.user-messages li').text()

        # Verify question is in db now
        question = Question.objects.filter(title='A test question')[0]
        eq_(question.locale, 'de')

    def test_full_workflow_inactive(self):
        u = User.objects.get(username='jsocol')
        u.is_active = False
        u.save()
        RegistrationProfile.objects.create_profile(u)
        response = self._post_new_question()
        eq_(200, response.status_code)

        # Verify question is in db now
        question = Question.objects.filter(title='A test question')[0]

        # Make sure question is not in questions list
        response = get(self.client, 'questions.questions')
        doc = pq(response.content)
        eq_(0, len(doc('li#question-%s' % question.id)))
        # And no confirmation email was sent (already sent on registration)
        eq_(0, len(mail.outbox))

    def test_invalid_type(self):
        """Providing an invalid type returns 400."""
        topic(title='Fix problems', slug='fix-problems', save=True)
        self.client.logout()

        url = urlparams(
            reverse('questions.aaq_step5', args=['desktop', 'fix-problems']),
            search='A test question')
        # Register before asking question
        data = {'username': 'testaaq',
                'password': 'testpass', 'password2': 'testpass',
                'email': 'testaaq@example.com'}
        data.update(**self.data)
        response = self.client.post(url, data, follow=True)
        eq_(400, response.status_code)
        assert 'Request type not recognized' in response.content

    @mock.patch.object(Site.objects, 'get_current')
    def test_register_through_aaq(self, get_current):
        """Registering through AAQ form sends confirmation email."""
        get_current.return_value.domain = 'testserver'
        topic(title='Fix problems', slug='fix-problems', save=True)
        self.client.logout()
        title = 'A test question'
        url = urlparams(
            reverse('questions.aaq_step5', args=['desktop', 'fix-problems']),
            search=title)
        # Register before asking question
        data = {'register': 'Register', 'username': 'testaaq',
                'password': 'testpass1', 'password2': 'testpass1',
                'email': 'testaaq@example.com'}
        data.update(**self.data)
        self.client.post(url, data, follow=True)

        # Confirmation email is sent
        eq_(1, len(mail.outbox))
        eq_(mail.outbox[0].subject,
            'Please confirm your Firefox Help question')
        assert mail.outbox[0].body.find('(%s)' % title) > 0

        # Finally post question
        self.client.post(url, self.data, follow=True)

        # Verify question is in db now
        question = Question.objects.filter(title=title)
        eq_(1, question.count())
        eq_('testaaq', question[0].creator.username)

        # And no confirmation email was sent (already sent on registration)
        # Note: there was already an email sent above
        eq_(1, len(mail.outbox))

    def test_invalid_product_404(self):
        url = reverse('questions.aaq_step2', args=['lipsum'])
        response = self.client.get(url)
        eq_(404, response.status_code)

    def test_invalid_category_302(self):
        url = reverse('questions.aaq_step3', args=['desktop', 'lipsum'])
        response = self.client.get(url)
        eq_(302, response.status_code)
