import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from celery import task

from kitsune.messages.models import InboxMessage
from kitsune.sumo.decorators import timeit
from kitsune.sumo.email_utils import make_mail, safe_translation, send_messages


log = logging.getLogger('k.task')


@task()
@timeit
def email_private_message(inbox_message_id):
    """Send notification of a new private message."""
    inbox_message = InboxMessage.objects.get(id=inbox_message_id)
    log.debug('Sending email for user (%s)' % (inbox_message.to,))

    user = inbox_message.to

    @safe_translation
    def _send_mail(locale):
        # Avoid circular import issues
        from kitsune.users.templatetags.jinja_helpers import display_name

        subject = _(u'[SUMO] You have a new private message from [{sender}]')
        subject = subject.format(
            sender=display_name(inbox_message.sender))

        msg_url = reverse('messages.read', kwargs={'msgid': inbox_message.id})
        settings_url = reverse('users.edit_settings')

        from kitsune.sumo.templatetags.jinja_helpers import add_utm
        context = {
            'sender': inbox_message.sender,
            'message': inbox_message.message,
            'message_html': inbox_message.content_parsed,
            'message_url': add_utm(msg_url, 'messages-new'),
            'unsubscribe_url': add_utm(settings_url, 'messages-new'),
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
