from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template import Context, loader

from tidings.events import InstanceEvent
from tower import ugettext as _

from questions.models import Question
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
        a new watcher."""
        subject = _('Please confirm your email address')
        email_kwargs = {'activation_url': cls._activation_url(watch),
                        'domain': Site.objects.get_current().domain,
                        'watch_description': cls.description_of_watch(watch)}
        template_path = 'questions/email/activate_watch.ltxt'
        message = loader.render_to_string(template_path, email_kwargs)
        return EmailMessage(subject, message,
                            settings.TIDINGS_FROM_ADDRESS, [email])

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

        watcher_subject = _(u'%s commented on a Firefox question '
                            "you're watching" % self.answer.creator.username)
        asker_subject = _(u'%s posted an answer to question "%s"' %
                          (self.answer.creator.username, self.instance.title))

        watcher_template = loader.get_template(
            'questions/email/new_answer.ltxt')
        asker_template = loader.get_template(
            'questions/email/new_answer_to_asker.ltxt')

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
            is_asker = asker_id == u.id
            content = (asker_template if is_asker else
                       watcher_template).render(Context(c))
            yield EmailMessage(asker_subject if is_asker
                                   else watcher_subject,
                               content,
                               settings.TIDINGS_FROM_ADDRESS,
                               [u.email])

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

        subject = _(u'Solution found to Firefox Help question')
        t = loader.get_template('questions/email/solution.ltxt')
        c = {'answerer': question.solution.creator,
             'asker': question.creator.username,
             'question_title': question.title,
             'host': Site.objects.get_current().domain,
             'solution_url': question.solution.get_absolute_url()}
        for u, w in users_and_watches:
            c['username'] = u.username  # '' if anonymous
            c['watch'] = w[0]  # TODO: Expose all watches.
            content = t.render(Context(c))
            yield EmailMessage(
                subject,
                content,
                settings.TIDINGS_FROM_ADDRESS,
                [u.email])

    @classmethod
    def description_of_watch(cls, watch):
        question = watch.content_object
        return _('Solution found for question: %s') % question.title
