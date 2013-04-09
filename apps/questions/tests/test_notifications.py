from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.core import mail

import mock
from nose.tools import eq_

from questions.events import QuestionReplyEvent, QuestionSolvedEvent
from questions.models import Question, Answer
from questions.tests import TestCaseBase
from sumo.tests import post, attrs_eq, starts_with
from users.models import Setting
from users.tests import user


# These mails are generated using reverse() calls, which return different
# results depending on whether a request is being processed at the time. This
# is because reverse() depends on a thread-local var which is set/unset at
# request boundaries by LocaleURLMiddleware. While a request is in progress,
# reverse() prepends a locale code; otherwise, it doesn't. Thus, when making a
# mock request that fires off a celery task that generates one of these emails,
# expect a locale in reverse()d URLs. When firing off a celery task outside the
# scope of a request, expect none.
#
# In production, with CELERY_ALWAYS_EAGER=False, celery tasks run in a
# different interpreter (with no access to the thread-local), so reverse() will
# never prepend a locale code unless passed force_locale=True. Thus, these
# test-emails with locale prefixes are not identical to the ones sent in
# production.
ANSWER_EMAIL_TO_ANONYMOUS = """rrosario commented on a Firefox question on testserver:

Lorem ipsum dolor sit amet?

https://testserver/en-US/questions/1#answer-{answer}

rrosario wrote:
"an answer"

See the comment:
https://testserver/en-US/questions/1#answer-{answer}

If this comment is helpful, vote on it:
https://testserver/en-US/questions/1/vote/{answer}?helpful

Help other Firefox users by browsing for unsolved questions on testserver:
https://testserver/questions?filter=unsolved

You might just make someone's day!

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe"""
ANSWER_EMAIL = u'Hi pcraciunoiu,\n\n' + ANSWER_EMAIL_TO_ANONYMOUS
ANSWER_EMAIL_TO_ASKER = """Hi jsocol,

rrosario has posted an answer to your question on testserver:
Lorem ipsum dolor sit amet?
https://testserver/en-US/questions/1#answer-{answer}

rrosario wrote:
"an answer"

See the answer:
https://testserver/en-US/questions/1#answer-{answer}

If this answer solves your problem, please mark it as "solved":"""
SOLUTION_EMAIL_TO_ANONYMOUS = \
"""We just wanted to let you know that pcraciunoiu has found a solution to a Firefox question that you're following.

The question:
Lorem ipsum dolor sit amet?

was marked as solved by its asker, jsocol.

You can view the solution using the link below.

Did this answer also help you? Did you find another post more helpful? Let other Firefox users know by voting next to the answer.

https://testserver/en-US/questions/1#answer-%s

Did you know that pcraciunoiu is a Firefox user just like you? Get started helping other Firefox users by browsing questions at https://testserver/questions?filter=unsolved -- you might just make someone's day!

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/"""
SOLUTION_EMAIL = 'Hi pcraciunoiu,\n\n' + SOLUTION_EMAIL_TO_ANONYMOUS


class NotificationsTests(TestCaseBase):
    """Test that notifications get sent."""

    def setUp(self):
        super(NotificationsTests, self).setUp()

    @mock.patch.object(QuestionReplyEvent, 'fire')
    def test_fire_on_new_answer(self, fire):
        """The event fires when a new answer is saved."""
        question = Question.objects.all()[0]
        Answer.objects.create(question=question, creator=user(save=True))

        assert fire.called

    @mock.patch.object(QuestionSolvedEvent, 'fire')
    def test_fire_on_solution(self, fire):
        """The event also fires when an answer is marked as a solution."""
        answer = Answer.objects.get(pk=1)
        question = answer.question
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'questions.solve', args=[question.id, answer.id])

        assert fire.called

    def _toggle_watch_question(self, event_type, turn_on=True):
        """Helper to watch/unwatch a question. Fails if called twice with
        the same turn_on value."""
        question = Question.objects.all()[0]
        self.client.login(username='pcraciunoiu', password='testpass')
        user = User.objects.get(username='pcraciunoiu')
        event_cls = (QuestionReplyEvent if event_type == 'reply'
                                        else QuestionSolvedEvent)
        # Make sure 'before' values are the reverse.
        if turn_on:
            assert not event_cls.is_notifying(user, question), (
                '%s should not be notifying.' % event_cls.__name__)
        else:
            assert event_cls.is_notifying(user, question), (
                '%s should be notifying.' % event_cls.__name__)

        url = 'questions.watch' if turn_on else 'questions.unwatch'
        data = {'event_type': event_type} if turn_on else {}
        post(self.client, url, data, args=[question.id])

        if turn_on:
            assert event_cls.is_notifying(user, question), (
                '%s should be notifying.' % event_cls.__name__)
        else:
            assert not event_cls.is_notifying(user, question), (
                '%s should not be notifying.' % event_cls.__name__)
        return question

    @mock.patch.object(Site.objects, 'get_current')
    @mock.patch.object(settings._wrapped, 'TIDINGS_CONFIRM_ANONYMOUS_WATCHES',
                       False)
    def test_solution_notification(self, get_current):
        """Assert that hitting the watch toggle toggles and that proper mails
        are sent to anonymous and registered watchers."""
        # TODO: Too monolithic. Split this test into several.
        get_current.return_value.domain = 'testserver'

        question = self._toggle_watch_question('solution', turn_on=True)
        QuestionSolvedEvent.notify('anon@ymous.com', question)

        answer = question.answers.all()[0]
        # Post a reply
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'questions.solve', args=[question.id, answer.id])

        # Order of emails is not important.
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Solution found to Firefox Help question')
        starts_with(mail.outbox[0].body, SOLUTION_EMAIL % answer.id)

        attrs_eq(mail.outbox[1], to=['anon@ymous.com'],
                 subject='Solution found to Firefox Help question')
        starts_with(mail.outbox[1].body,
                    SOLUTION_EMAIL_TO_ANONYMOUS % answer.id)

        self._toggle_watch_question('solution', turn_on=False)

    @mock.patch.object(Site.objects, 'get_current')
    @mock.patch.object(settings._wrapped, 'TIDINGS_CONFIRM_ANONYMOUS_WATCHES',
                       False)
    def test_answer_notification(self, get_current):
        """Assert that hitting the watch toggle toggles and that proper mails
        are sent to anonymous users, registered users, and the question
        asker."""
        # TODO: This test is way too monolithic, and the fixtures encode
        # assumptions that aren't obvious here. Split this test into about 5,
        # each of which tests just 1 thing. Consider using instantiation
        # helpers.
        get_current.return_value.domain = 'testserver'

        # An arbitrary registered user (pcraciunoiu) watches:
        question = self._toggle_watch_question('reply', turn_on=True)
        # An anonymous user watches:
        QuestionReplyEvent.notify('anon@ymous.com', question)
        # The question asker (jsocol) watches:
        QuestionReplyEvent.notify(question.creator, question)

        # Post a reply
        self.client.login(username='rrosario', password='testpass')
        post(self.client, 'questions.reply', {'content': 'an answer'},
             args=[question.id])

        answer = Answer.uncached.filter().order_by('-id')[0]

        # Order of emails is not important.
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='%s commented on a Firefox question '
                         "you're watching" % answer.creator.username)
        starts_with(mail.outbox[0].body, ANSWER_EMAIL.format(answer=answer.id))

        attrs_eq(mail.outbox[1], to=[question.creator.email],
                 subject='%s posted an answer to your question "%s"' %
                         (answer.creator.username, question.title))
        starts_with(mail.outbox[1].body, ANSWER_EMAIL_TO_ASKER.format(
            answer=answer.id))

        attrs_eq(mail.outbox[2], to=['anon@ymous.com'],
                 subject="%s commented on a Firefox question you're watching" %
                         answer.creator.username)
        starts_with(mail.outbox[2].body, ANSWER_EMAIL_TO_ANONYMOUS.format(
            answer=answer.id))

        self._toggle_watch_question('reply', turn_on=False)

    @mock.patch.object(Site.objects, 'get_current')
    def test_autowatch_reply(self, get_current):
        get_current.return_value.domain = 'testserver'

        user = User.objects.get(username='timw')
        t1, t2 = Question.objects.filter(is_locked=False)[0:2]
        assert not QuestionReplyEvent.is_notifying(user, t1)
        assert not QuestionReplyEvent.is_notifying(user, t2)

        self.client.login(username='timw', password='testpass')
        s = Setting.objects.create(user=user, name='questions_watch_after_reply',
                                   value='True')
        data = {'content': 'some content'}
        post(self.client, 'questions.reply', data, args=[t1.id])
        assert QuestionReplyEvent.is_notifying(user, t1)

        s.value = 'False'
        s.save()
        post(self.client, 'questions.reply', data, args=[t2.id])
        assert not QuestionReplyEvent.is_notifying(user, t2)

    @mock.patch.object(Site.objects, 'get_current')
    def test_solution_notification_deleted(self, get_current):
        """Calling QuestionSolvedEvent.fire() should not query the
        questions_question table.

        This test attempts to simulate the replication lag presumed to cause
        bug 585029.

        """
        get_current.return_value.domain = 'testserver'

        answer = Answer.objects.get(pk=1)
        question = Question.objects.get(pk=1)
        question.solution = answer
        question.save()

        a_user = User.objects.get(username='pcraciunoiu')
        QuestionSolvedEvent.notify(a_user, question)
        event = QuestionSolvedEvent(answer)

        # Delete the question, pretend it hasn't been replicated yet
        Question.objects.get(pk=question.pk).delete()

        event.fire(exclude=question.creator)
        eq_(1, len(mail.outbox))
