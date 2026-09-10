import waffle
from django.conf import settings
from django_jinja import library


@library.global_function
def chat_is_available(request, products=None) -> bool:
    """Whether to show the Zendesk chat widget on a page about these products.

    Pass the products the page is about. Any one of them being a chat product is
    enough. Omit them for a page that isn't about a product, such as the home
    page, which skips the product check but is still gated on everything else.
    """
    if not (waffle.switch_is_active("zendesk-chat") and settings.ZENDESK_CHAT_WIDGET_KEY):
        return False

    if not request.user.is_authenticated:
        return False

    if request.LANGUAGE_CODE not in settings.ZENDESK_CHAT_LOCALES:
        return False

    if products is not None:
        slugs = settings.ZENDESK_CHAT_PRODUCT_SLUGS
        if not any(product.slug in slugs for product in products):
            return False

    # TODO: Replace with eligibility check.
    return True
