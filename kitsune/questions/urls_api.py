from django.conf.urls import patterns, url

from kitsune.questions import api


# API urls
urlpatterns = patterns(
    '',
    # All questions
    url(r'^$', api.QuestionList.as_view()),
    # A particular question
    url(r'^(?P<id>\d+)/?$', api.QuestionDetail.as_view()),
    # Answers for a question
    url(r'^(?P<question_id>\d+)/answers/?$', api.AnswerList.as_view()),

    # All answers
    url(r'^answers/?$', api.AnswerList.as_view()),
    # A particular answer
    url(r'^answers/(?P<id>\d+)?$', api.AnswerDetail.as_view()),
)
