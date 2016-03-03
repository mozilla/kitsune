from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _

from babel.dates import format_datetime
from pytz import timezone
from tidings.events import InstanceEvent

from kitsune.users.auth import get_auth_str
from kitsune.questions.models import Question
from kitsune.sumo import email_utils
from kitsune.sumo.templatetags.jinja_helpers import urlparams, add_utm
from kitsune.sumo.urlresolvers import reverse


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

        @email_utils.safe_translation
        def _make_mail(locale):
            subject = _('Please confirm your email address')
            context = {
                'activation_url': cls._activation_url(watch),
                'domain': Site.objects.get_current().domain,
                'watch_description': cls.description_of_watch(watch)}

            mail = email_utils.make_mail(
                subject=subject,
                text_template='questions/email/activate_watch.ltxt',
                html_template='questions/email/activate_watch.html',
                context_vars=context,
                from_email=settings.TIDINGS_FROM_ADDRESS,
                to_email=email)

            return mail

        if watch.user:
            locale = watch.user.profile.locale
        else:
            locale = 'en-US'

        return _make_mail(locale)

    @classmethod
    def _activation_url(cls, watch):
        url = reverse(
            'questions.activate_watch', args=[watch.id, watch.secret])
        return add_utm(url, 'questions-activate')


class QuestionReplyEvent(QuestionEvent):
    """An event which fires when a new answer is posted for a question"""
    event_type = 'question reply'

    def _mails(self, users_and_watches):
        """Send one kind of mail to the asker and another to other watchers."""
        # Cache answer.question, similar to caching solution.question below.
        self.answer.question = self.instance
        asker_id = self.answer.question.creator.id

        c = {'answer': self.answer.content,
             'answer_html': self.answer.content_parsed,
             'answerer': self.answer.creator,
             'question_title': self.instance.title,
             'host': Site.objects.get_current().domain}

        @email_utils.safe_translation
        def _make_mail(locale, user, context):
            # Avoid circular import issues
            from kitsune.users.templatetags.jinja_helpers import display_name

            is_asker = asker_id == user.id
            if is_asker:
                subject = _(u'%s posted an answer to your question "%s"' %
                            (display_name(self.answer.creator),
                             self.instance.title))
                text_template = 'questions/email/new_answer_to_asker.ltxt'
                html_template = 'questions/email/new_answer_to_asker.html'
            else:
                subject = _(u'Re: %s' % self.instance.title)
                text_template = 'questions/email/new_answer.ltxt'
                html_template = 'questions/email/new_answer.html'

            mail = email_utils.make_mail(
                subject=subject,
                text_template=text_template,
                html_template=html_template,
                context_vars=context,
                from_email='Mozilla Support Forum '
                           '<no-reply@support.mozilla.org>',
                to_email=user.email)

            return mail

        for u, w in users_and_watches:
            auth_str = get_auth_str(self.answer.question.creator)

            c['answer_url'] = self.answer.get_absolute_url()
            c['helpful_url'] = self.answer.get_helpful_answer_url()
            c['solution_url'] = self.answer.get_solution_url(watch=w[0])

            for k in ['answer_url', 'helpful_url', 'solution_url']:
                c[k] = add_utm(
                    urlparams(c[k], auth=auth_str), 'questions-reply')

            c['to_user'] = u
            c['watch'] = w[0]  # TODO: Expose all watches.

            # u here can be a Django User model or a Tidings EmailUser
            # model. In the case of the latter, there is no associated
            # profile, so we set the locale to en-US.
            if hasattr(u, 'profile'):
                locale = u.profile.locale
                tzinfo = u.profile.timezone
            else:
                locale = 'en-US'
                tzinfo = timezone(settings.TIME_ZONE)

            c['created'] = format_datetime(self.answer.created, tzinfo=tzinfo,
                                           locale=locale.replace('-', '_'))

            yield _make_mail(locale, u, c)

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

        @email_utils.safe_translation
        def _make_mail(locale, user, context):
            subject = _(u'Solution found to Firefox Help question')

            mail = email_utils.make_mail(
                subject=subject,
                text_template='questions/email/solution.ltxt',
                html_template='questions/email/solution.html',
                context_vars=context,
                from_email=settings.TIDINGS_FROM_ADDRESS,
                to_email=user.email)

            return mail

        solution_url = add_utm(
            question.solution.get_absolute_url(), 'questions-solved')

        c = {'answerer': question.solution.creator,
             'asker': question.creator,
             'question_title': question.title,
             'host': Site.objects.get_current().domain,
             'solution_url': solution_url}

        for u, w in users_and_watches:
            c['to_user'] = u  # '' if anonymous
            c['watch'] = w[0]  # TODO: Expose all watches.

            # u here can be a Django User model or a Tidings EmailUser
            # model. In the case of the latter, there is no associated
            # profile, so we set the locale to en-US.
            if hasattr(u, 'profile'):
                locale = u.profile.locale
            else:
                locale = 'en-US'

            yield _make_mail(locale, u, c)

    @classmethod
    def description_of_watch(cls, watch):
        question = watch.content_object
        return _('Solution found for question: %s') % question.title
