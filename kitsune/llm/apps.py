from django.apps import AppConfig


class LLMConfig(AppConfig):
    name = "kitsune.llm"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from kitsune.llm.utils import get_llm

        # pre-warm the LLM cache
        get_llm()
