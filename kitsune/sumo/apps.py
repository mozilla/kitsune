from django.apps.config import AppConfig


class SumoConfig(AppConfig):
    name = 'kitsune.sumo'

    def ready(self):
        """ Bootstrapping stuff """

        # Install gettext translations
        # Note: we'll remove these things with django-jinja
        import jingo
        from django.utils import translation
        jingo.get_env().install_gettext_translations(translation, newstyle=True)
        jingo.load_helpers()
