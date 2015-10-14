from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response

from kitsune.questions.models import QuestionLocale
from kitsune.lib.sumo_locales import LOCALES


@api_view(['GET'])
def locales_api_view(request):
    """API endpoint listing all supported locales"""
    locales = {}
    for lang in settings.SUMO_LANGUAGES:
        # FIXME: Need a better way to skip fake locales.
        if lang == 'xx':
            continue

        # FIXME: should we add something based on SIMPLE_WIKI_LANGUAGES?
        locale = {
            'name': LOCALES[lang].english,
            'localized_name': LOCALES[lang].native,
        }
        try:
            QuestionLocale.objects.get(locale=lang)
            locale['aaq_enabled'] = True
        except QuestionLocale.DoesNotExist:
            locale['aaq_enabled'] = False
        locales[lang] = locale

    return Response(locales)
