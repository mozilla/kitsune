from django.db.models.signals import post_save
from django.dispatch import receiver

from kitsune.wiki.models import Document


@receiver(
    post_save,
    sender=Document,
    dispatch_uid="wiki.reject_obsolete_translations",
)
def reject_obsolete_translations(sender, instance, created, **kwargs):
    """
    When a document is updated, reject any of its unreviewed machine translations
    that may have become obsolete.
    """
    if created:
        # A freshly created document can't lead to obsolete translations.
        return

    from kitsune.wiki.services import HybridTranslationService

    HybridTranslationService().reject_obsolete_translations(instance)
