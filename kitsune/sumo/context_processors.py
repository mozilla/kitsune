from django.conf import settings
from django.utils import translation


def global_settings(request):
    """Adds settings to the context."""
    return {'settings': settings}


def i18n(request):
    return {'LANG': (settings.LANGUAGE_URL_MAP.get(translation.get_language())
                     or translation.get_language()),
            'DIR': 'rtl' if translation.get_language_bidi() else 'ltr'}


def geoip_cache_detector(request):
    cookies = getattr(request, 'COOKIES', {})
    has_geoip = ('geoip_country_name' in cookies and
                 'geoip_country_code' in cookies)
    is_en_us = getattr(request, 'LANGUAGE_CODE', 'en-US') == 'en-US'

    return {'include_geoip': is_en_us and not has_geoip}
