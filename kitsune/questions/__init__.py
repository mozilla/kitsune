from django.apps import AppConfig

import actstream.registry


default_app_config = 'kitsune.questions.QuestionsConfig'


class QuestionsConfig(AppConfig):
    name = 'kitsune.questions'

    def ready(self):
        Question = self.get_model('Question')
        actstream.registry.register(Question)
        Answer = self.get_model('Answer')
        actstream.registry.register(Answer)
