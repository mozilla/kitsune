from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    name = "kitsune.questions"

    def ready(self):
        from kitsune.questions.badges import register_signals

        import actstream.registry

        Question = self.get_model("Question")
        actstream.registry.register(Question)
        Answer = self.get_model("Answer")
        actstream.registry.register(Answer)

        # register signals for badges
        register_signals()
