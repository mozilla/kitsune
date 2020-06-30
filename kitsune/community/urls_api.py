from django.conf.urls import url

from kitsune.community import api


urlpatterns = [
    url("^topcontributors/questions/$", api.TopContributorsQuestions.as_view()),
    url("^topcontributors/l10n/$", api.TopContributorsLocalization.as_view()),
]
