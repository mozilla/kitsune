from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from kitsune.lib.sumo_locales import LOCALES
from kitsune.questions.models import QuestionLocale


@api_view(["GET"])
def locales_api_view(request):
    """API endpoint listing all supported locales"""
    locales = {}
    for lang in settings.SUMO_LANGUAGES:
        # FIXME: Need a better way to skip fake locales.
        if lang == "xx":
            continue

        locale = {
            "name": LOCALES[lang].english,
            "localized_name": LOCALES[lang].native,
            "aaq_enabled": QuestionLocale.objects.filter(locale=lang).exists(),
        }
        locales[lang] = locale

    return Response(locales)
