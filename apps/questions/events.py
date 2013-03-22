from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage

from tidings.events import InstanceEvent
from tower import ugettext as _

from questions.models import Question
from sumo import email_utils
from sumo.urlresolvers import reverse


class QuestionEvent(InstanceEvent):
    """Abstract common functionality between question events."""
    content_type = Question

    def __init__(self, answer):
        super(QuestionEvent, self).__init__(answer.question)
        self.answer = answer

    @classmethod
    def _activation_email(cls, watch, email):
        """Return an EmailMessage containing the activation URL to be sent to
        a new watcher.
        """
        # If the watch has an associated user, use that
        # locale. Otherwise it's an anonymous watch and we don't know
        # what locale they want, so we give them en-US.
        if watch.user:
            locale = watch.user.profile.locale
        else:
            locale = 'en-US'

        @email_utils.safe_translation
        def _make_mail(locale):
            subject = _('Please confirm your email address')
            email_kwargs = {'activation_url': cls._activation_url(watch),
                            'domain': Site.objects.get_current().domain,
                            'watch_description': cls.description_of_watch(watch)}
            template = 'questions/email/activate_watch.ltxt'
            message = email_utils.render_email(template, email_kwargs)

            return EmailMessage(subject, message,
                                settings.TIDINGS_FROM_ADDRESS, [email])

        return _make_mail(locale)

    @classmethod
    def _activation_url(cls, watch):
        return reverse('questions.activate_watch',
                       args=[watch.id, watch.secret])


class QuestionReplyEvent(QuestionEvent):
    """An event which fires when a new answer is posted for a question"""
    event_type = 'question reply'

    def _mails(self, users_and_watches):
        """Send one kind of mail to the asker and another to other watchers."""
        # Cache answer.question, similar to caching solution.question below.
        self.answer.question = self.instance
        asker_id = self.answer.question.creator.id

        c = {'answer': self.answer.content,
             'answerer': self.answer.creator.username,
             'question_title': self.instance.title,
             'host': Site.objects.get_current().domain,
             'answer_url': self.answer.get_absolute_url()}

        for u, w in users_and_watches:
            c['helpful_url'] = self.answer.get_helpful_answer_url()
            c['solution_url'] = self.answer.get_solution_url(watch=w[0])
            c['username'] = u.username
            c['watch'] = w[0]  # TODO: Expose all watches.

            # u here can be a Django User model or a Tidings EmailUser
            # model. In the case of the latter, there is no associated
            # profile, so we set the locale to en-US.
            if hasattr(u, 'profile'):
                locale = u.profile.locale
            else:
                locale = 'en-US'

            @email_utils.safe_translation
            def _make_mail(locale):
                is_asker = asker_id == u.id
                if is_asker:
                    subject = _(u'%s posted an answer to your question "%s"' %
                                (self.answer.creator.username, self.instance.title))
                    template = 'questions/email/new_answer_to_asker.ltxt'

                else:
                    subject = _(u'%s commented on a Firefox question '
                                "you're watching" % self.answer.creator.username)
                    template = 'questions/email/new_answer.ltxt'

                msg = email_utils.render_email(template, c)

                return EmailMessage(subject,
                                    msg,
                                    settings.TIDINGS_FROM_ADDRESS,
                                    [u.email])

            yield _make_mail(locale)

    @classmethod
    def description_of_watch(cls, watch):
        return _('New answers for question: %s') % watch.content_object.title


class QuestionSolvedEvent(QuestionEvent):
    """An event which fires when a Question gets solved"""
    event_type = 'question solved'

    def _mails(self, users_and_watches):
        question = self.instance
        # Cache solution.question as a workaround for replication lag
        # (bug 585029)
        question.solution = self.answer
        question.solution.question = question

        c = {'answerer': question.solution.creator,
             'asker': question.creator.username,
             'question_title': question.title,
             'host': Site.objects.get_current().domain,
             'solution_url': question.solution.get_absolute_url()}

        for u, w in users_and_watches:
            c['username'] = u.username  # '' if anonymous
            c['watch'] = w[0]  # TODO: Expose all watches.

            # u here can be a Django User model or a Tidings EmailUser
            # model. In the case of the latter, there is no associated
            # profile, so we set the locale to en-US.
            if hasattr(u, 'profile'):
                locale = u.profile.locale
            else:
                locale = 'en-US'

            @email_utils.safe_translation
            def _make_mail(locale):
                subject = _(u'Solution found to Firefox Help question')
                content = email_utils.render_email(
                    'questions/email/solution.ltxt', c)

                return EmailMessage(subject, content,
                                    settings.TIDINGS_FROM_ADDRESS, [u.email])

            yield _make_mail(locale)

    @classmethod
    def description_of_watch(cls, watch):
        question = watch.content_object
        return _('Solution found for question: %s') % question.title
