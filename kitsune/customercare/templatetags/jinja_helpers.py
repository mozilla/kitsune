from typing import TYPE_CHECKING

from django.conf import settings
from django_jinja import library

from kitsune.customercare.utils import is_chat_enabled, resolve_chat_eligibility

if TYPE_CHECKING:
    from kitsune.products.models import Product


@library.global_function
def chat_is_available(request, product: Product | None) -> bool:
    """Whether to show the Zendesk chat widget on a page about this product."""
    if not product:
        return False

    if not is_chat_enabled():
        return False

    if request.LANGUAGE_CODE not in settings.ZENDESK_CHAT_ENABLED_LOCALES:
        return False

    eligibility = resolve_chat_eligibility(request.user, product)

    request._show_chat = eligibility.eligible

    return eligibility.eligible


@library.global_function
def to_zendesk_locale(locale: str) -> str:
    """Returns the Zendesk locale for the given SUMO locale."""
    return locale if locale == "en-US" else locale.lower()
