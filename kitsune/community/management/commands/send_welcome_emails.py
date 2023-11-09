from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.utils.translation import gettext as _

from kitsune.questions.models import Answer
from kitsune.sumo.email_utils import make_mail, safe_translation, send_messages
from kitsune.users.models import Profile
from kitsune.wiki.models import Revision


class Command(BaseCommand):
    help = "Send a welcome email to first time contributors."

    def handle(self, **options):
        """
        Anyone who has made a contribution more than 24 hours ago and has not
        already gotten a welcome email should get a welcome email.
        """

        wait_period = datetime.now() - timedelta(hours=24)
        messages = []
        context = {"host": Site.objects.get_current().domain}

        # Answers

        answer_filter = Q(created__range=(datetime.min, wait_period))
        answer_filter &= ~Q(question__creator=F("creator"))
        answer_filter &= Q(creator__profile__first_answer_email_sent=False)

        answer_recipient_ids = set(
            Answer.objects.filter(answer_filter).values_list("creator", flat=True)
        )

        @safe_translation
        def _make_answer_email(locale, to):
            return make_mail(
                subject=_("Thank you for your contribution to Mozilla Support!"),
                text_template="community/email/first_answer.ltxt",
                html_template="community/email/first_answer.html",
                context_vars=context,
                from_email=settings.TIDINGS_FROM_ADDRESS,
                to_email=to.email,
            )

        for user in User.objects.filter(id__in=answer_recipient_ids):
            messages.append(_make_answer_email(user.profile.locale, user))

        # Localization

        l10n_filter = Q(created__range=(datetime.min, wait_period))
        l10n_filter &= ~Q(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
        l10n_filter &= Q(creator__profile__first_l10n_email_sent=False)

        l10n_recipient_ids = set(
            Revision.objects.filter(l10n_filter).values_list("creator", flat=True)
        )

        # This doesn't need localized, and so don't need the `safe_translation` helper.
        for user in User.objects.filter(id__in=l10n_recipient_ids):
            messages.append(
                make_mail(
                    subject="Thank you for your contribution to Mozilla Support!",
                    text_template="community/email/first_l10n.ltxt",
                    html_template="community/email/first_l10n.html",
                    context_vars=context,
                    from_email=settings.TIDINGS_FROM_ADDRESS,
                    to_email=user.email,
                )
            )

        # Release the Kraken!
        send_messages(messages)

        Profile.objects.filter(user__id__in=answer_recipient_ids).update(
            first_answer_email_sent=True
        )
        Profile.objects.filter(user__id__in=l10n_recipient_ids).update(first_l10n_email_sent=True)
