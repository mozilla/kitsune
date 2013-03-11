from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage, get_connection

import bleach
from celery.task import task
from tower import ugettext as _

from announcements.models import Announcement
from sumo.email_utils import uselocale, render_email


@task
def send_group_email(announcement_id):
    """Build and send the announcement emails to a group."""
    try:
        announcement = Announcement.objects.get(pk=announcement_id)
    except Announcement.DoesNotExist:
        return
    connection = get_connection(fail_silently=True)
    connection.open()
    group = announcement.group
    users = User.objects.filter(groups__in=[group])
    plain_content = bleach.clean(announcement.content_parsed,
                                 tags=[], strip=True).strip()
    email_kwargs = {'content': plain_content,
                    'domain': Site.objects.get_current().domain}
    template = 'announcements/email/announcement.ltxt'
    try:
        for u in users:
            # Localize email each time.
            with uselocale(u.profile.locale or settings.LANGUAGE_CODE):
                subject = _('New announcement for {group}').format(
                    group=group.name)
                msg = render_email(template, email_kwargs)

            m = EmailMessage(subject,
                             msg,
                             settings.TIDINGS_FROM_ADDRESS,
                             [u.email])
            connection.send_messages([m])

    finally:
        connection.close()
