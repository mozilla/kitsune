from rest_framework import routers

from kitsune.questions.api import QuestionViewSet

router = routers.SimpleRouter()
router.register(r'question', QuestionViewSet)
urlpatterns = router.urls
