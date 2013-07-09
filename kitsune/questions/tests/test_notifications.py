from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_

from kitsune.questions.events import QuestionReplyEvent, QuestionSolvedEvent
from kitsune.questions.models import Question, Answer
from kitsune.questions.tests import TestCaseBase, question, answer
from kitsune.sumo.tests import post, attrs_eq, starts_with
from kitsune.users.models import Setting
from kitsune.users.tests import user


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
ANSWER_EMAIL_TO_ANONYMOUS = """{replier} commented on a Firefox question on testserver:

{title}

https://testserver/en-US/questions/{question_id}#answer-{answer_id}

{replier} wrote:
"{content}"

See the comment:
https://testserver/en-US/questions/{question_id}#answer-{answer_id}

If this comment is helpful, vote on it:
https://testserver/en-US/questions/{question_id}/vote/{answer_id}?helpful

Help other Firefox users by browsing for unsolved questions on testserver:
https://testserver/questions?filter=unsolved

You might just make someone's day!

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe"""
ANSWER_EMAIL = u'Hi {to_user},\n\n' + ANSWER_EMAIL_TO_ANONYMOUS
ANSWER_EMAIL_TO_ASKER = """Hi {asker},

{replier} has posted an answer to your question on testserver:
{title}
https://testserver/en-US/questions/{question_id}#answer-{answer_id}

{replier} wrote:
"{content}"

See the answer:
https://testserver/en-US/questions/{question_id}#answer-{answer_id}

If this answer solves your problem, please mark it as "solved":"""
SOLUTION_EMAIL_TO_ANONYMOUS = \
"""We just wanted to let you know that {replier} has found a solution to a Firefox question that you're following.

The question:
{title}

was marked as solved by its asker, {asker}.

You can view the solution using the link below.

Did this answer also help you? Did you find another post more helpful? Let other Firefox users know by voting next to the answer.

https://testserver/en-US/questions/{question_id}#answer-{answer_id}

Did you know that {replier} is a Firefox user just like you? Get started helping other Firefox users by browsing questions at https://testserver/questions?filter=unsolved -- you might just make someone's day!

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/"""
SOLUTION_EMAIL = 'Hi {to_user},\n\n' + SOLUTION_EMAIL_TO_ANONYMOUS


class NotificationsTests(TestCaseBase):
    """Test that notifications get sent."""

    def setUp(self):
        super(NotificationsTests, self).setUp()

    @mock.patch.object(QuestionReplyEvent, 'fire')
    def test_fire_on_new_answer(self, fire):
        """The event fires when a new answer is saved."""
        q = question(save=True)
        Answer.objects.create(question=q, creator=user(save=True))

        assert fire.called

    @mock.patch.object(QuestionSolvedEvent, 'fire')
    def test_fire_on_solution(self, fire):
        """The event also fires when an answer is marked as a solution."""
        a = answer(save=True)
        q = a.question

        self.client.login(username=q.creator, password='testpass')
        post(self.client, 'questions.solve', args=[q.id, a.id])

        assert fire.called

    def _toggle_watch_question(self, event_type, user, turn_on=True):
        """Helper to watch/unwatch a question. Fails if called twice with
        the same turn_on value."""
        q = question(save=True)

        self.client.login(username=user.username, password='testpass')

        event_cls = (QuestionReplyEvent if event_type == 'reply'
                                        else QuestionSolvedEvent)
        # Make sure 'before' values are the reverse.
        if turn_on:
            assert not event_cls.is_notifying(user, q), (
                '%s should not be notifying.' % event_cls.__name__)
        else:
            assert event_cls.is_notifying(user, q), (
                '%s should be notifying.' % event_cls.__name__)

        url = 'questions.watch' if turn_on else 'questions.unwatch'
        data = {'event_type': event_type} if turn_on else {}
        post(self.client, url, data, args=[q.id])

        if turn_on:
            assert event_cls.is_notifying(user, q), (
                '%s should be notifying.' % event_cls.__name__)
        else:
            assert not event_cls.is_notifying(user, q), (
                '%s should not be notifying.' % event_cls.__name__)
        return q

    @mock.patch.object(Site.objects, 'get_current')
    @mock.patch.object(settings._wrapped, 'TIDINGS_CONFIRM_ANONYMOUS_WATCHES',
                       False)
    def test_solution_notification(self, get_current):
        """Assert that hitting the watch toggle toggles and that proper mails
        are sent to anonymous and registered watchers."""
        # TODO: Too monolithic. Split this test into several.
        get_current.return_value.domain = 'testserver'

        u = user(save=True)
        q = self._toggle_watch_question('solution', u, turn_on=True)
        QuestionSolvedEvent.notify('anon@ymous.com', q)

        a = answer(question=q, save=True)

        # Mark a solution
        self.client.login(username=q.creator.username, password='testpass')
        post(self.client, 'questions.solve', args=[q.id, a.id])

        # Order of emails is not important.
        # Note: we skip the first email because it is a reply notification
        # to the asker.
        attrs_eq(mail.outbox[1], to=[u.email],
                 subject='Solution found to Firefox Help question')
        starts_with(mail.outbox[1].body, SOLUTION_EMAIL.format(
            to_user=u.username,
            replier=a.creator.username,
            title=q.title,
            asker=q.creator.username,
            question_id=q.id,
            answer_id=a.id))

        attrs_eq(mail.outbox[2], to=['anon@ymous.com'],
                 subject='Solution found to Firefox Help question')
        starts_with(mail.outbox[2].body, SOLUTION_EMAIL_TO_ANONYMOUS.format(
            replier=a.creator.username,
            title=q.title,
            asker=q.creator.username,
            question_id=q.id,
            answer_id=a.id))

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

        # An arbitrary registered user watches:
        watcher = user(save=True)
        q = self._toggle_watch_question('reply', watcher, turn_on=True)

        # An anonymous user watches:
        QuestionReplyEvent.notify('anon@ymous.com', q)

        # The question asker watches:
        QuestionReplyEvent.notify(q.creator, q)

        # Post a reply
        replier = user(save=True)
        self.client.login(username=replier.username, password='testpass')
        post(self.client, 'questions.reply', {'content': 'an answer'},
             args=[q.id])

        a = Answer.uncached.filter().order_by('-id')[0]

        # Order of emails is not important.
        eq_(3, len(mail.outbox))

        emails_to = [m.to[0] for m in mail.outbox]

        i = emails_to.index(watcher.email)
        attrs_eq(mail.outbox[i], to=[watcher.email],
                 subject='%s commented on a Firefox question '
                         "you're watching" % a.creator.username)
        starts_with(mail.outbox[i].body, ANSWER_EMAIL.format(
            to_user=watcher.username,
            title=q.title,
            content=a.content,
            replier=replier.username,
            question_id=q.id,
            answer_id=a.id))

        i = emails_to.index(q.creator.email)
        attrs_eq(mail.outbox[i], to=[q.creator.email],
                 subject='%s posted an answer to your question "%s"' %
                         (a.creator.username, q.title))
        starts_with(mail.outbox[i].body, ANSWER_EMAIL_TO_ASKER.format(
            asker=q.creator.username,
            title=q.title,
            content=a.content,
            replier=replier.username,
            question_id=q.id,
            answer_id=a.id))

        i = emails_to.index('anon@ymous.com')
        attrs_eq(mail.outbox[i], to=['anon@ymous.com'],
                 subject="%s commented on a Firefox question you're watching" %
                         a.creator.username)
        starts_with(mail.outbox[i].body, ANSWER_EMAIL_TO_ANONYMOUS.format(
            title=q.title,
            content=a.content,
            replier=replier.username,
            question_id=q.id,
            answer_id=a.id))

    @mock.patch.object(Site.objects, 'get_current')
    def test_autowatch_reply(self, get_current):
        get_current.return_value.domain = 'testserver'

        u = user(save=True)
        t1 = question(save=True)
        t2 = question(save=True)
        assert not QuestionReplyEvent.is_notifying(u, t1)
        assert not QuestionReplyEvent.is_notifying(u, t2)

        self.client.login(username=u.username, password='testpass')
        s = Setting.objects.create(user=u, name='questions_watch_after_reply',
                                   value='True')
        data = {'content': 'some content'}
        post(self.client, 'questions.reply', data, args=[t1.id])
        assert QuestionReplyEvent.is_notifying(u, t1)

        s.value = 'False'
        s.save()
        post(self.client, 'questions.reply', data, args=[t2.id])
        assert not QuestionReplyEvent.is_notifying(u, t2)

    @mock.patch.object(Site.objects, 'get_current')
    def test_solution_notification_deleted(self, get_current):
        """Calling QuestionSolvedEvent.fire() should not query the
        questions_question table.

        This test attempts to simulate the replication lag presumed to cause
        bug 585029.

        """
        get_current.return_value.domain = 'testserver'

        a = answer(save=True)
        q = a.question
        q.solution = a
        q.save()

        a_user = a.creator
        QuestionSolvedEvent.notify(a_user, q)
        event = QuestionSolvedEvent(a)

        # Delete the question, pretend it hasn't been replicated yet
        Question.objects.get(pk=q.pk).delete()

        event.fire(exclude=q.creator)

        # There should be a reply notification and a solved notification.
        eq_(2, len(mail.outbox))
        eq_('Solution found to Firefox Help question', mail.outbox[1].subject)
