from django.apps import AppConfig
from django.conf import settings


class LLMConfig(AppConfig):
    name = "kitsune.llm"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from kitsune.llm.utils import get_llm

        if settings.GOOGLE_CLOUD_PROJECT:
            # pre-warm the LLM cache
            get_llm()
