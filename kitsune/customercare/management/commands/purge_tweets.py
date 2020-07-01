import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from multidb.pinning import pin_this_thread

from kitsune.customercare.models import Tweet

log = logging.getLogger("k.twitter")


class Command(BaseCommand):
    help = "Periodically purge old tweets for each locale."

    def handle(self, **options):
        """
        This does a lot of DELETEs on master, so it shouldn't run too frequently.
        Probably once every hour or more.
        """
        # Pin to master
        pin_this_thread()

        # Build list of tweets to delete, by id.
        for locale in settings.SUMO_LANGUAGES:
            locale = settings.LOCALES[locale].iso639_1
            # Some locales don't have an iso639_1 code, too bad for them.
            if not locale:
                continue
            oldest = _get_oldest_tweet(locale, settings.CC_MAX_TWEETS)
            if oldest:
                log.debug(
                    "Truncating tweet list: Removing tweets older than %s, for [%s]."
                    % (oldest.created, locale)
                )
                Tweet.objects.filter(locale=locale, created__lte=oldest.created).delete()


def _get_oldest_tweet(locale, n=0):
    """Returns the nth oldest tweet per locale, defaults to newest."""
    try:
        return Tweet.objects.filter(locale=locale).order_by("-created")[n]
    except IndexError:
        return None
