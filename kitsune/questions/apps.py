from django.apps import AppConfig


def is_installed(model_class):
    """
    This is a fix for django-activity-stream 1.4.0 that
    should fix an issue. Evidently django-activity-stream
    will have a release just for 4.1 at some point...
    https://github.com/justquick/django-activity-stream/issues/515
    """
    return model_class._meta.app_config is not None


class QuestionsConfig(AppConfig):
    name = "kitsune.questions"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import actstream.registry

        from kitsune.questions.badges import register_signals

        """
        Drop the following line once that release happens
        """
        actstream.registry.is_installed = is_installed

        Question = self.get_model("Question")
        actstream.registry.register(Question)
        Answer = self.get_model("Answer")
        actstream.registry.register(Answer)

        # register signals for badges
        register_signals()
