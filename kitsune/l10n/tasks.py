from celery import shared_task
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, Value
import logging

from kitsune.l10n.models import MachineTranslationConfiguration
from kitsune.l10n.utils import build_message, get_l10n_bot, run_with_pg_lock
from kitsune.l10n.wiki import (
    create_machine_translations,
    manage_existing_machine_translations,
)
from kitsune.messages.utils import send_message
from kitsune.wiki.models import Document, Locale


log = logging.getLogger("k.l10n.tasks")
log.setLevel(logging.INFO)


@shared_task
@run_with_pg_lock
def handle_wiki_localization(document_id=None):
    """
    Task that handles all aspects of machine translations for KB articles.
    If a document id is provided, the work is limited to that document,
    otherwise all documents are considered.
    """
    log.info(f"Starting handle_wiki_localization(document_id={document_id})...")

    if document_id is not None:
        try:
            doc = Document.objects.select_related(
                "parent",
                "current_revision",
                "latest_localizable_revision",
            ).get(id=document_id)
        except Document.DoesNotExist:
            return
    else:
        doc = None

    # Freshly load the configuration for machine translations.
    mt_config = MachineTranslationConfiguration.load()

    # Make any changes as needed to existing machine translations.
    modified = manage_existing_machine_translations(mt_config, doc)
    # Generate new machine translations as needed.
    created = create_machine_translations(mt_config, doc.parent if doc and doc.parent else doc)

    # Notify each of the locale teams as needed.
    for locale in set(modified.keys()) | set(created.keys()):
        modified_for_locale = modified.get(locale, {})
        created_for_locale = created.get(locale, {})
        text = build_message(
            mt_config,
            creations_awaiting_review=created_for_locale.get("awaiting_review"),
            creations_already_approved=created_for_locale.get("already_approved"),
            rejections=modified_for_locale.get("rejections"),
            pre_review_approvals=modified_for_locale.get("pre_review_approvals"),
            post_rejection_approvals=modified_for_locale.get("post_rejection_approvals"),
        )
        send_message_to_locale_team.delay(locale, text)

    log.info(f"Completed handle_wiki_localization(document_id={document_id})")


@shared_task
def send_message_to_locale_team(locale, text):
    """
    Task that sends the given message to the leaders and reviewers of the given locale.
    """
    try:
        team = (
            Locale.objects.filter(locale=locale)
            .annotate(
                usernames_of_leaders=ArrayAgg(
                    "leaders__username",
                    filter=Q(leaders__is_active=True),
                    default=Value([]),
                ),
                usernames_of_reviewers=ArrayAgg(
                    "reviewers__username",
                    filter=Q(reviewers__is_active=True),
                    default=Value([]),
                ),
            )
            .get()
        )
    except Locale.DoesNotExist:
        return

    if not (usernames := team.usernames_of_leaders + team.usernames_of_reviewers):
        return

    # Send the message to the locale team's active leaders and reviewers.
    to = dict(users=usernames)
    log.info(
        f'Sending the following message to the "{locale}" locale team:\n'
        f'{"-" * 40}\nUsernames: {", ".join(usernames)}\n'
        f'{"-" * 40}\n{text}\n{"-" * 40}'
    )
    send_message(to, text=text, sender=get_l10n_bot())
