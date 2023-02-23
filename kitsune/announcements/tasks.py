import bleach
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.translation import gettext as _

from kitsune.announcements.models import Announcement
from kitsune.sumo.email_utils import make_mail, safe_translation, send_messages


@shared_task
def send_group_email(announcement_id):
    """Build and send the announcement emails to a group."""
    try:
        announcement = Announcement.objects.get(pk=announcement_id)
    except Announcement.DoesNotExist:
        return

    groups = announcement.groups.all()
    users = User.objects.filter(groups__in=groups).distinct()
    plain_content = bleach.clean(announcement.content_parsed, tags=[], strip=True).strip()
    email_kwargs = {
        "content": plain_content,
        "content_html": announcement.content_parsed,
        "domain": Site.objects.get_current().domain,
    }
    text_template = "announcements/email/announcement.ltxt"
    html_template = "announcements/email/announcement.html"

    @safe_translation
    def _make_mail(locale, user):
        if groups.count() == 1:
            subject = _(f"New announcement for {groups[0].name}")
        else:
            subject = _(f"New announcement for groups [{', '.join([g.name for g in groups])}]")

        mail = make_mail(
            subject=subject,
            text_template=text_template,
            html_template=html_template,
            context_vars=email_kwargs,
            from_email=settings.TIDINGS_FROM_ADDRESS,
            to_email=user.email,
        )

        return mail

    messages = []
    for u in users:
        # Localize email each time.
        locale = u.profile.locale or settings.LANGUAGE_CODE
        messages.append(_make_mail(locale, u))

    send_messages(messages)
