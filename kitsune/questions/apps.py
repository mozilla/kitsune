from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    name = "kitsune.questions"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import actstream.registry

        from kitsune.questions.badges import register_signals

        Question = self.get_model("Question")
        actstream.registry.register(Question)
        Answer = self.get_model("Answer")
        actstream.registry.register(Answer)

        # register signals for badges
        register_signals()
