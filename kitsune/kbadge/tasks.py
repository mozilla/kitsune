from celery import task
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.translation import pgettext
from django.utils.translation import ugettext as _
from sentry_sdk import capture_exception

from kitsune.kbadge.models import Award
from kitsune.sumo import email_utils


@task()
def send_award_notification(award_id: int):
    """Sends the award notification email

    :arg award: the Award instance

    """
    try:
        award = Award.objects.get(id=award_id)
    except Award.DoesNotExist as err:
        capture_exception(err)
        return

    @email_utils.safe_translation
    def _make_mail(locale, context, email):

        subject = _("You were awarded the '{title}' badge!").format(
            title=pgettext("DB: badger.Badge.title", award.badge.title)
        )

        mail = email_utils.make_mail(
            subject=subject,
            text_template="kbadge/email/award_notification.ltxt",
            html_template="kbadge/email/award_notification.html",
            context_vars=context,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=email,
        )

        return mail

    msg = _make_mail(
        locale=award.user.profile.locale,
        context={"host": Site.objects.get_current().domain, "award": award, "badge": award.badge,},
        email=award.user.email,
    )

    # FIXME: this sends emails to the person who was awarded the
    # badge. Should we also send an email to the person who awarded
    # the badge? Currently, I think we shouldn't.

    email_utils.send_messages([msg])
