from django.apps import AppConfig


class WikiConfig(AppConfig):
    name = "kitsune.wiki"

    def ready(self):
        from kitsune.wiki.badges import register_signals

        # register signals for badges
        register_signals()
