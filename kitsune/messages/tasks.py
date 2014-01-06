import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from celery.task import task
from tower import ugettext as _

from kitsune.messages.models import InboxMessage
from kitsune.sumo.email_utils import make_mail, safe_translation, send_messages


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
            'message_html': inbox_message.content_parsed,
            'message_url': reverse('messages.read',
                                   kwargs={'msgid': inbox_message.id}),
            'unsubscribe_url': reverse('users.edit_settings'),
            'host': Site.objects.get_current().domain}

        mail = make_mail(subject=subject,
                         text_template='messages/email/private_message.ltxt',
                         html_template='messages/email/private_message.html',
                         context_vars=context,
                         from_email=settings.TIDINGS_FROM_ADDRESS,
                         to_email=inbox_message.to.email)

        send_messages([mail])

    if hasattr(user, 'profile'):
        locale = user.profile.locale
    else:
        locale = settings.WIKI_DEFAULT_LANGUAGE

    _send_mail(locale)
