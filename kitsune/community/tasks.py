import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext as _

from kitsune.questions.models import Answer
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.sumo.email_utils import make_mail, safe_translation, send_messages
from kitsune.users.models import Profile
from kitsune.users.utils import get_community_team_member_info
from kitsune.wiki.models import Revision

log = logging.getLogger("k.task")


@shared_task
@skip_if_read_only_mode
def send_welcome_emails() -> None:
    """
    Anyone who has made a contribution more than 24 hours ago and has not
    already gotten a welcome email should get a welcome email.
    """
    log.info("Sending welcome emails")

    wait_period = timezone.now() - timedelta(hours=24)
    messages = []

    base_context = {"host": Site.objects.get_current().domain}

    # Answers

    answer_filter = Q(created__range=(datetime.min, wait_period))
    answer_filter &= ~Q(question__creator=F("creator"))
    answer_filter &= Q(creator__profile__first_answer_email_sent=False)

    answer_recipient_ids = set(
        Answer.objects.filter(answer_filter).values_list("creator", flat=True)
    )

    # Get team member info for first_answer emails
    answer_team_info = get_community_team_member_info("first_answer")

    @safe_translation
    def _make_answer_email(locale, to):
        context = {**base_context, **answer_team_info, "user": to}

        return make_mail(
            subject=_("Congrats on your first forum reply!"),
            text_template="community/email/first_answer.ltxt",
            html_template="community/email/first_answer.html",
            context_vars=context,
            from_email=settings.TIDINGS_FROM_ADDRESS,
            to_email=to.email,
        )

    for user in User.objects.filter(id__in=answer_recipient_ids):
        messages.append(_make_answer_email(user.profile.locale, user))

    num_first_answer_messages = len(messages)

    # Localization

    l10n_filter = Q(created__range=(datetime.min, wait_period))
    l10n_filter &= ~Q(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
    l10n_filter &= Q(creator__profile__first_l10n_email_sent=False)

    l10n_recipient_ids = set(
        Revision.objects.filter(l10n_filter).values_list("creator", flat=True)
    )

    # Get team member info for first_l10n emails
    l10n_team_info = get_community_team_member_info("first_l10n")

    # This doesn't need localized, and so don't need the `safe_translation` helper.
    for user in User.objects.filter(id__in=l10n_recipient_ids):
        context = {**base_context, **l10n_team_info, "user": user}

        messages.append(
            make_mail(
                subject="Congrats on your first article revision!",
                text_template="community/email/first_l10n.ltxt",
                html_template="community/email/first_l10n.html",
                context_vars=context,
                from_email=settings.TIDINGS_FROM_ADDRESS,
                to_email=user.email,
            )
        )

    num_first_l10n_messages = len(messages) - num_first_answer_messages

    log.info(f"Sending {num_first_answer_messages} welcome emails for forum replies")
    log.info(f"Sending {num_first_l10n_messages} welcome emails for localization")

    # Release the Kraken!
    send_messages(messages)

    Profile.objects.filter(user__id__in=answer_recipient_ids).update(first_answer_email_sent=True)
    Profile.objects.filter(user__id__in=l10n_recipient_ids).update(first_l10n_email_sent=True)
