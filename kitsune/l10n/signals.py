from django.db.models.signals import post_save
from django.dispatch import receiver

from kitsune.l10n.models import MachineTranslationConfiguration
from kitsune.l10n.utils import manage_heartbeat
from kitsune.l10n.wiki import is_suitable_for_l10n
from kitsune.l10n.tasks import handle_wiki_localization
from kitsune.wiki.signals import revision_approved


@receiver(revision_approved, dispatch_uid="l10.handle_wiki_localization_in_real_time")
def handle_wiki_localization_in_real_time(sender, revision, **kwargs):
    """
    A revision has been approved for a document, so we may need to perform
    some localization work.
    """
    if is_suitable_for_l10n(revision.document.original):
        handle_wiki_localization.delay(revision.document.id)


@receiver(
    post_save, sender=MachineTranslationConfiguration, dispatch_uid="l10.manage_heartbeat_on_save"
)
def manage_heartbeat_on_save(sender, instance, created, **kwargs):
    """
    Create, modify, or delete the heartbeat periodic task, if necessary, after the
    MachineTranslationConfiguration singleton has been created or modified.
    """
    manage_heartbeat(instance.heartbeat_period)
