from django_jinja import library

from kitsune.wiki.models import Document


@library.global_function
def is_localized(slug, request_language_code):
    """
    Check the article is localized to the requested language.
    For the default language assume yes.
    """
    return Document.objects.filter(locale=request_language_code, slug=slug).exclude(
        current_revision=None).exists() or Document.objects.filter(locale=request_language_code,
                                                                   parent__slug=slug).exclude(
        current_revision=None).exists()
