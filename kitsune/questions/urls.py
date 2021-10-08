from django.conf import settings
from django.urls import path

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
    path("", views.product_list, name="questions.home"),
    path(
        "answer-preview-async$", views.answer_preview_async, name="questions.answer_preview_async"
    ),
    path("dashboard/metrics$", views.metrics, name="questions.metrics"),
    path("dashboard/metrics/<str:locale_code>", views.metrics, name="questions.locale_metrics"),
    # AAQ
    path("new", views.aaq, name="questions.aaq_step1"),
    path("new/<str:product_key>", views.aaq_step2, name="questions.aaq_step2"),
    path("new/<str:product_key>/form", views.aaq_step3, name="questions.aaq_step3"),
    # maintain backwards compatibility with old aaq urls:
    path("new/<str:product_key>/<str:category_key>", views.aaq_step3, name="questions.aaq_step3"),
    # TODO: Factor out `/(?P<question_id>\d+)` below
    path("<int:question_id>", views.question_details, name="questions.details"),
    path("<int:question_id>/edit", views.edit_question, name="questions.edit_question"),
    path("<int:question_id>/edit-details", views.edit_details, name="questions.edit_details"),
    path("<int:question_id>/reply", views.reply, name="questions.reply"),
    path("<int:question_id>/delete", views.delete_question, name="questions.delete"),
    path("<int:question_id>/lock", views.lock_question, name="questions.lock"),
    path("<int:question_id>/archive", views.archive_question, name="questions.archive"),
    path(
        "<int:question_id>/delete/<int:answer_id>",
        views.delete_answer,
        name="questions.delete_answer",
    ),
    path(
        "<int:question_id>/edit/<int:answer_id>", views.edit_answer, name="questions.edit_answer"
    ),
    path("<int:question_id>/solve/<int:answer_id>", views.solve, name="questions.solve"),
    path("<int:question_id>/unsolve/<int:answer_id>", views.unsolve, name="questions.unsolve"),
    path("<int:question_id>/vote", views.question_vote, name="questions.vote"),
    path(
        "<int:question_id>/vote/<int:answer_id>", views.answer_vote, name="questions.answer_vote"
    ),
    path("<int:question_id>/add-tag", views.add_tag, name="questions.add_tag"),
    path("<int:question_id>/remove-tag", views.remove_tag, name="questions.remove_tag"),
    path("<int:question_id>/add-tag-async", views.add_tag_async, name="questions.add_tag_async"),
    path(
        "<int:question_id>/remove-tag-async",
        views.remove_tag_async,
        name="questions.remove_tag_async",
    ),
    # Feeds
    # Note: this needs to be above questions.list because "feed"
    # matches the product slug regex.
    path("feed", questions_feed_view, name="questions.feed"),
    path("<int:question_id>/feed", answers_feed_view, name="questions.answers.feed"),
    path("tagged/<str:tag_slug>/feed", tagged_feed_view, name="questions.tagged_feed"),
    # Mark as spam
    path("mark_spam", views.mark_spam, name="questions.mark_spam"),
    path("unmark_spam", views.unmark_spam, name="questions.unmark_spam"),
    # Question lists
    path("<str:product_slug>", views.question_list, name="questions.list"),
    # Flag content ("Report this post")
    path("<int:object_id>/flag", flagit_views.flag, {"model": Question}, name="questions.flag"),
    path(
        "<int:question_id>/flag/<int:object_id>",
        flagit_views.flag,
        {"model": Answer},
        name="questions.answer_flag",
    ),
    # Subcribe by email
    path("<int:question_id>/watch", views.watch_question, name="questions.watch"),
    path("<int:question_id>/unwatch", views.unwatch_question, name="questions.unwatch"),
    path(
        "confirm/<int:watch_id>/<str:secret>",
        views.activate_watch,
        name="questions.activate_watch",
    ),
    path(
        "unsubscribe/<int:watch_id>/<str:secret>",
        views.unsubscribe_watch,
        name="questions.unsubscribe",
    ),
]
