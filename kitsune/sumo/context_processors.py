from django.conf import settings
from django.utils import translation


def global_settings(request):
    """Adds settings to the context."""
    return {'settings': settings}


def i18n(request):
    return {'LANG': (settings.LANGUAGE_URL_MAP.get(translation.get_language())
                     or translation.get_language()),
            'DIR': 'rtl' if translation.get_language_bidi() else 'ltr'}
