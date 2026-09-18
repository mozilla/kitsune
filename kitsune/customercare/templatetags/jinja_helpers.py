from typing import TYPE_CHECKING

from django.conf import settings
from django_jinja import library

from kitsune.customercare.utils import resolve_chat_eligibility

if TYPE_CHECKING:
    from kitsune.products.models import Product


@library.global_function
def chat_is_available(request, product: Product | None) -> bool:
    """Whether to show the Zendesk chat widget on a page about this product."""
    if not product:
        return False

    eligibility = resolve_chat_eligibility(request.user, product)

    request._show_chat = eligibility.eligible

    return eligibility.eligible


@library.global_function
def select_zendesk_locale(locale: str) -> str:
    """Select the Zendesk locale for the given SUMO locale."""
    return (
        locale.lower()
        if locale in settings.ZENDESK_CHAT_SUPPORTED_NON_ENGLISH_LOCALES
        else "en-US"
    )
