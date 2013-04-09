import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse

from celery.task import task
from tower import ugettext as _

from messages.models import InboxMessage
from sumo.email_utils import safe_translation, render_email, send_messages


log = logging.getLogger('k.task')


@task
def email_private_message(inbox_message_id):
    """Send notification of a new private message."""
    inbox_message = InboxMessage.objects.get(id=inbox_message_id)
    log.debug('Sending email for user (%s)' % (inbox_message.to,))

    user = inbox_message.to

    @safe_translation
    def _send_mail(locale):
        subject = _(u'[SUMO] You have a new private message from [{sender}]')
        subject = subject.format(sender=inbox_message.sender.username)

        context = {
            'sender': inbox_message.sender.username,
            'message': inbox_message.message,
            'url': reverse('messages.read',
                           kwargs={'msgid': inbox_message.id}),
            'unsubscribe_url': reverse('users.edit_settings'),
            'host': Site.objects.get_current().domain}

        text_template = 'messages/email/private_message.ltxt'
        html_template = None

        msg = EmailMultiAlternatives(
            subject,
            render_email(text_template, context),
            settings.TIDINGS_FROM_ADDRESS,
            [inbox_message.to.email])

        if html_template:
            msg.attach_alternative(
                render_email(html_template, context), 'text/html')

        send_messages([msg])

    if hasattr(user, 'profile'):
        locale = user.profile.locale
    else:
        locale = settings.WIKI_DEFAULT_LANGUAGE

    _send_mail(locale)
