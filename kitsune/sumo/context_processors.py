from django.conf import settings
from django.utils import translation

from kitsune.questions.models import QuestionLocale


def global_settings(request):
    """Adds settings to the context."""
    return {'settings': settings}


def i18n(request):
    return {'LANG': (settings.LANGUAGE_URL_MAP.get(translation.get_language()) or
                     translation.get_language()),
            'DIR': 'rtl' if translation.get_language_bidi() else 'ltr'}


def aaq_languages(request):
    """Adds the list of AAQ languages to the context."""
    return {'AAQ_LANGUAGES': QuestionLocale.objects.locales_list()}
