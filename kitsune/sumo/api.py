from django.conf import settings
from rest_framework.exceptions import APIException


class CORSMixin(object):
    def finalize_response(self, request, response, *args, **kwargs):
        response = (super(CORSMixin, self)
                    .finalize_response(request, response, *args, **kwargs))
        response['Access-Control-Allow-Origin'] = '*'
        return response


class GenericAPIException(APIException):
    def __init__(self, status_code, detail, **kwargs):
        self.status_code = status_code
        self.detail = detail
        for key, val in kwargs.items():
            setattr(self, key, val)


class LocaleNegotiationMixin(object):
    """A mixin for CBV to select a locale based on Accept-Language headers."""

    def get_locale(self):
        acceptable_locales = self.request.META.get('HTTP_ACCEPT_LANGUAGE',
                                                   'en-US')
        acceptable_locales = acceptable_locales.split(',')
        acceptable_locales = [l.split(';')[0] for l in acceptable_locales]

        sumo_languages = dict((l.lower(), l) for l in settings.SUMO_LANGUAGES)
        non_supported_locales = dict((k.lower(), v)
                                     for k, v
                                     in settings.NON_SUPPORTED_LOCALES.items())

        for locale in acceptable_locales:
            locale = locale.lower()
            if locale in sumo_languages:
                return sumo_languages[locale]
            if locale in non_supported_locales:
                locale = non_supported_locales[locale]
                if locale is not None:
                    return locale

        return settings.WIKI_DEFAULT_LANGUAGE
