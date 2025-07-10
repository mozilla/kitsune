from rest_framework import routers

from kitsune.questions.api import AnswerViewSet, QuestionViewSet

router = routers.SimpleRouter()
router.register(r"question", QuestionViewSet)
router.register(r"answer", AnswerViewSet)
urlpatterns = router.urls
