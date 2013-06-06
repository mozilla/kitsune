from django.conf import settings
from django.utils import translation

from kitsune.wiki.config import OPERATING_SYSTEMS, FIREFOX_VERSIONS


def global_settings(request):
    """Adds settings to the context."""
    return {'settings': settings}


def for_data(request):
    os = dict([(o.slug, o.id) for o in OPERATING_SYSTEMS])
    version = dict([(v.slug, v.id) for v in FIREFOX_VERSIONS])
    return {'for_os': os, 'for_version': version}


def i18n(request):
    return {'LANG': settings.LANGUAGE_URL_MAP.get(translation.get_language())
                    or translation.get_language(),
            'DIR': 'rtl' if translation.get_language_bidi() else 'ltr'}
