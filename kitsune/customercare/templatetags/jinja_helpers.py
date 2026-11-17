from typing import TYPE_CHECKING

from django.conf import settings
from django_jinja import library

from kitsune.products.routing import route_support
from kitsune.products.utils import get_support_company, get_support_locale

if TYPE_CHECKING:
    from kitsune.products.models import Product


@library.global_function
def chat_is_available(request, product: Product | None) -> bool:
    """Whether to show the Zendesk chat widget on a page about this product."""
    if not product:
        return False

    eligibility = route_support(request, product).chat

    request._show_chat = eligibility.eligible

    return eligibility.eligible


@library.global_function
def chat_conversation_tags(product: Product) -> str:
    """Space-separated tags the widget puts on a new chat conversation."""
    tags = settings.ZENDESK_CHAT_TAGS.split()
    tags.append(f"{settings.ZENDESK_CHAT_PRODUCT_TAG_PREFIX}{product.slug}")
    return " ".join(tags)


@library.global_function
def chat_locale(request, product: Product) -> str:
    """The widget's locale: the page's, if the company's contracts for the product allow it."""
    locale = request.LANGUAGE_CODE
    company = get_support_company(request)
    if company:
        locale = get_support_locale(company, locale, product)
    # The widget takes lower-case codes like "pt-br"; English stays "en-US".
    return locale if locale == settings.WIKI_DEFAULT_LANGUAGE else locale.lower()
