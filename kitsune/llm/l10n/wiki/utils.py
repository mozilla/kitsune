from django.conf import settings


def get_language_in_english(locale: str) -> str:
    """
    Returns the name of the locale in English, for example "it" returns "Italian"
    and "pt-BR" returns "Portuguese (Brazilian)".
    """
    return settings.LOCALES[locale].english
