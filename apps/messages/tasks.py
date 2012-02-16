import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template import Context, loader

from messages.models import InboxMessage
from celery.decorators import task
from tower import ugettext as _


log = logging.getLogger('k.task')


@task
def email_private_message(inbox_message_id):
    """Send notification of a new private message."""
    inbox_message = InboxMessage.objects.get(id=inbox_message_id)
    log.debug('Sending email for user (%s)' % (inbox_message.to,))
    subject = _(u'[SUMO] You have a new private message from [{sender}]')
    subject = subject.format(sender=inbox_message.sender.username)
    t = loader.get_template('messages/email/private_message.ltxt')
    unsubscribe_url = reverse('users.edit_settings')
    url = reverse('messages.read', kwargs={'msgid': inbox_message.id})
    content = t.render(Context({'sender': inbox_message.sender.username,
                                'message': inbox_message.message,
                                'url': url,
                                'unsubscribe_url': unsubscribe_url,
                                'host': Site.objects.get_current().domain}))
    send_mail(subject, content, settings.TIDINGS_FROM_ADDRESS,
              [inbox_message.to.email])
