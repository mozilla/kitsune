from django.apps import AppConfig

from kitsune.wiki.badges import register_signals


default_app_config = 'kitsune.wiki.WikiConfig'


class WikiConfig(AppConfig):
    name = 'kitsune.wiki'

    def ready(self):
        # register signals for badges
        register_signals()
