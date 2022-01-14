from django.conf import settings
from django.urls import re_path

from kitsune.flagit import views as flagit_views
from kitsune.questions import views
from kitsune.questions.feeds import AnswersFeed, QuestionsFeed, TaggedQuestionsFeed
from kitsune.questions.models import Answer, Question
from kitsune.sumo.views import handle404

if settings.DISABLE_FEEDS:
    questions_feed_view = handle404
    answers_feed_view = handle404
    tagged_feed_view = handle404
else:
    questions_feed_view = QuestionsFeed()
    answers_feed_view = AnswersFeed()
    tagged_feed_view = TaggedQuestionsFeed()

urlpatterns = [
    re_path(r"^$", views.product_list, name="questions.home"),
    re_path(
        r"^/answer-preview-async$",
        views.answer_preview_async,
        name="questions.answer_preview_async",
    ),
    re_path(r"^/dashboard/metrics$", views.metrics, name="questions.metrics"),
    re_path(
        r"^/dashboard/metrics/(?P<locale_code>[^/]+)$",
        views.metrics,
        name="questions.locale_metrics",
    ),
    # AAQ
    re_path(r"^/new$", views.aaq, name="questions.aaq_step1"),
    re_path(r"^/new/(?P<product_key>[\w\-]+)$", views.aaq_step2, name="questions.aaq_step2"),
    re_path(r"^/new/(?P<product_key>[\w\-]+)/form$", views.aaq_step3, name="questions.aaq_step3"),
    # maintain backwards compatibility with old aaq urls:
    re_path(
        r"^/new/(?P<product_key>[\w\-]+)/(?P<category_key>[\w\-]+)",
        views.aaq_step3,
        name="questions.aaq_step3",
    ),
    # TODO: Factor out `/(?P<question_id>\d+)` below
    re_path(r"^/(?P<question_id>\d+)$", views.question_details, name="questions.details"),
    re_path(r"^/(?P<question_id>\d+)/edit$", views.edit_question, name="questions.edit_question"),
    re_path(
        r"^/(?P<question_id>\d+)/edit-details$", views.edit_details, name="questions.edit_details"
    ),
    re_path(r"^/(?P<question_id>\d+)/reply$", views.reply, name="questions.reply"),
    re_path(r"^/(?P<question_id>\d+)/delete$", views.delete_question, name="questions.delete"),
    re_path(r"^/(?P<question_id>\d+)/lock$", views.lock_question, name="questions.lock"),
    re_path(r"^/(?P<question_id>\d+)/archive$", views.archive_question, name="questions.archive"),
    re_path(
        r"^/(?P<question_id>\d+)/delete/(?P<answer_id>\d+)$",
        views.delete_answer,
        name="questions.delete_answer",
    ),
    re_path(
        r"^/(?P<question_id>\d+)/edit/(?P<answer_id>\d+)$",
        views.edit_answer,
        name="questions.edit_answer",
    ),
    re_path(
        r"^/(?P<question_id>\d+)/solve/(?P<answer_id>\d+)$", views.solve, name="questions.solve"
    ),
    re_path(
        r"^/(?P<question_id>\d+)/unsolve/(?P<answer_id>\d+)$",
        views.unsolve,
        name="questions.unsolve",
    ),
    re_path(r"^/(?P<question_id>\d+)/vote$", views.question_vote, name="questions.vote"),
    re_path(
        r"^/(?P<question_id>\d+)/vote/(?P<answer_id>\d+)$",
        views.answer_vote,
        name="questions.answer_vote",
    ),
    re_path(r"^/(?P<question_id>\d+)/add-tag$", views.add_tag, name="questions.add_tag"),
    re_path(r"^/(?P<question_id>\d+)/remove-tag$", views.remove_tag, name="questions.remove_tag"),
    re_path(
        r"^/(?P<question_id>\d+)/add-tag-async$",
        views.add_tag_async,
        name="questions.add_tag_async",
    ),
    re_path(
        r"^/(?P<question_id>\d+)/remove-tag-async$",
        views.remove_tag_async,
        name="questions.remove_tag_async",
    ),
    # Feeds
    # Note: this needs to be above questions.list because "feed"
    # matches the product slug regex.
    re_path(r"^/feed$", questions_feed_view, name="questions.feed"),
    re_path(r"^/(?P<question_id>\d+)/feed$", answers_feed_view, name="questions.answers.feed"),
    re_path(
        r"^/tagged/(?P<tag_slug>[\w\-]+)/feed$", tagged_feed_view, name="questions.tagged_feed"
    ),
    # Mark as spam
    re_path(r"^/mark_spam$", views.mark_spam, name="questions.mark_spam"),
    re_path(r"^/unmark_spam$", views.unmark_spam, name="questions.unmark_spam"),
    # Question lists
    re_path(r"^/(?P<product_slug>[\w+\-\,]+)$", views.question_list, name="questions.list"),
    # Flag content ("Report this post")
    re_path(
        r"^/(?P<object_id>\d+)/flag$",
        flagit_views.flag,
        {"model": Question},
        name="questions.flag",
    ),
    re_path(
        r"^/(?P<question_id>\d+)/flag/(?P<object_id>\d+)$",
        flagit_views.flag,
        {"model": Answer},
        name="questions.answer_flag",
    ),
    # Subcribe by email
    re_path(r"^/(?P<question_id>\d+)/watch$", views.watch_question, name="questions.watch"),
    re_path(r"^/(?P<question_id>\d+)/unwatch$", views.unwatch_question, name="questions.unwatch"),
    re_path(
        r"^/confirm/(?P<watch_id>\d+)/(?P<secret>\w+)$",
        views.activate_watch,
        name="questions.activate_watch",
    ),
    re_path(
        r"^/unsubscribe/(?P<watch_id>\d+)/(?P<secret>\w+)$",
        views.unsubscribe_watch,
        name="questions.unsubscribe",
    ),
]
