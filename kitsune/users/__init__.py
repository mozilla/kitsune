from django.utils.translation import gettext_lazy as _lazy

SUMO_BOT_BIO = _lazy(
    "SUMO Bot is a system tool used by the Customer Experience team to provide and maintain "
    "content on the Mozilla Support website. You might see SUMO Bot appear in the forums as "
    "a placeholder for users whose Mozilla Account was deleted, due to inactivity or user "
    "request, but whose contributed content is kept in order to preserve important "
    "context in the forum post. SUMO Bot might also be used to make announcements or "
    "provide additional information in various support channels. Please note that SUMO Bot "
    "is not an active user account and will not respond to direct mentions, private "
    "messages, or forum thread replies."
)

L10N_BOT_BIO = _lazy(
    "L10n Bot is a system account used by the Customer Experience team to provide "
    "machine-translated content on the Mozilla Support website."
)

DEACTIVATIONS_PER_PAGE = 50
