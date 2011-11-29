
import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template import Context, loader

from celery.decorators import task
from tower import ugettext as _

from sumo.urlresolvers import reverse


log = logging.getLogger('k.task')


@task
def email_private_message(inbox_message):
    """Send notification of a new private message."""
    log.debug('Sending email for user (%s)' % (inbox_message.to,))
    subject = _(u'You have a new private message from [{sender}]')
    subject = subject.format(sender=inbox_message.sender.username)
    t = loader.get_template('messages/email/private_message.ltxt')
    url = reverse('messages.read', kwargs={'msgid': inbox_message.id})
    content = t.render(Context({'sender': inbox_message.sender.username,
                                'message': inbox_message.message,
                                'url': url,
                                'host': Site.objects.get_current().domain}))
    send_mail(subject, content, settings.TIDINGS_FROM_ADDRESS,
              [inbox_message.to.email])
