from django.conf import settings
from django.conf.urls import url

from kitsune.questions import views
from kitsune.questions.feeds import (
    QuestionsFeed, AnswersFeed, TaggedQuestionsFeed)
from kitsune.questions.models import Question, Answer
from kitsune.flagit import views as flagit_views
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
    url(r'^$', views.product_list, name='questions.home'),

    url(r'^/answer-preview-async$', views.answer_preview_async,
        name='questions.answer_preview_async'),
    url(r'^/dashboard/metrics$', views.metrics, name='questions.metrics'),
    url(r'^/dashboard/metrics/(?P<locale_code>[^/]+)$', views.metrics,
        name='questions.locale_metrics'),

    # AAQ
    url(r'^/new$', views.aaq, name='questions.aaq_step1'),
    url(r'^/new/confirm$', views.aaq_confirm, name='questions.aaq_confirm'),
    url(r'^/new/(?P<product_key>[\w\-]+)$',
        views.aaq_step2, name='questions.aaq_step2'),
    url(r'^/new/(?P<product_key>[\w\-]+)/(?P<category_key>[\w\-]+)$',
        views.aaq_step3, name='questions.aaq_step3'),
    url(r'^/new/(?P<product_key>[\w\-]+)/(?P<category_key>[\w\-]+)/search$',
        views.aaq_step4, name='questions.aaq_step4'),
    url(r'^/new/(?P<product_key>[\w\-]+)/(?P<category_key>[\w\-]+)/form$',
        views.aaq_step5, name='questions.aaq_step5'),

    # AAQ flow for Marketplace
    url(r'^/marketplace$', views.marketplace, name='questions.marketplace_aaq'),
    url(r'^/marketplace/success$',
        views.marketplace_success, name='questions.marketplace_aaq_success'),
    url(r'^/marketplace/refund$', views.marketplace_refund,
        name='questions.marketplace_refund'),
    url(r'^/marketplace/developer-request$', views.marketplace_developer_request,
        name='questions.marketplace_developer_request'),
    url(r'^/marketplace/(?P<category_slug>[\w\-]+)$',
        views.marketplace_category, name='questions.marketplace_aaq_category'),

    # TODO: Factor out `/(?P<question_id>\d+)` below
    url(r'^/(?P<question_id>\d+)$', views.question_details,
        name='questions.details'),
    url(r'^/(?P<question_id>\d+)/edit$',
        views.edit_question, name='questions.edit_question'),
    url(r'^/(?P<question_id>\d+)/edit-details$',
        views.edit_details, name='questions.edit_details'),
    url(r'^/(?P<question_id>\d+)/reply$', views.reply, name='questions.reply'),
    url(r'^/(?P<question_id>\d+)/delete$', views.delete_question,
        name='questions.delete'),
    url(r'^/(?P<question_id>\d+)/lock$', views.lock_question,
        name='questions.lock'),
    url(r'^/(?P<question_id>\d+)/archive$', views.archive_question,
        name='questions.archive'),
    url(r'^/(?P<question_id>\d+)/delete/(?P<answer_id>\d+)$',
        views.delete_answer, name='questions.delete_answer'),
    url(r'^/(?P<question_id>\d+)/edit/(?P<answer_id>\d+)$', views.edit_answer,
        name='questions.edit_answer'),
    url(r'^/(?P<question_id>\d+)/solve/(?P<answer_id>\d+)$', views.solve,
        name='questions.solve'),
    url(r'^/(?P<question_id>\d+)/unsolve/(?P<answer_id>\d+)$', views.unsolve,
        name='questions.unsolve'),
    url(r'^/(?P<question_id>\d+)/vote$', views.question_vote,
        name='questions.vote'),
    url(r'^/(?P<question_id>\d+)/vote/(?P<answer_id>\d+)$',
        views.answer_vote, name='questions.answer_vote'),
    url(r'^/(?P<question_id>\d+)/add-tag$', views.add_tag,
        name='questions.add_tag'),
    url(r'^/(?P<question_id>\d+)/remove-tag$', views.remove_tag,
        name='questions.remove_tag'),
    url(r'^/(?P<question_id>\d+)/add-tag-async$', views.add_tag_async,
        name='questions.add_tag_async'),
    url(r'^/(?P<question_id>\d+)/remove-tag-async$', views.remove_tag_async,
        name='questions.remove_tag_async'),
    url(r'^/(?P<question_id>\d+)/screen-share/$', views.screen_share,
        name='questions.screen_share'),

    # Feeds
    # Note: this needs to be above questions.list because "feed"
    # matches the product slug regex.
    url(r'^/feed$', questions_feed_view, name='questions.feed'),
    url(r'^/(?P<question_id>\d+)/feed$', answers_feed_view,
        name='questions.answers.feed'),
    url(r'^/tagged/(?P<tag_slug>[\w\-]+)/feed$', tagged_feed_view,
        name='questions.tagged_feed'),

    # Mark as spam
    url(r'^/mark_spam$', views.mark_spam, name='questions.mark_spam'),
    url(r'^/unmark_spam$', views.unmark_spam, name='questions.unmark_spam'),

    # Question lists
    url(r'^/(?P<product_slug>[\w+\-\,]+)$', views.question_list,
        name='questions.list'),

    # Flag content ("Report this post")
    url(r'^/(?P<object_id>\d+)/flag$', flagit_views.flag,
        {'model': Question}, name='questions.flag'),
    url(r'^/(?P<question_id>\d+)/flag/(?P<object_id>\d+)$', flagit_views.flag,
        {'model': Answer}, name='questions.answer_flag'),

    # Subcribe by email
    url(r'^/(?P<question_id>\d+)/watch$', views.watch_question,
        name='questions.watch'),
    url(r'^/(?P<question_id>\d+)/unwatch$', views.unwatch_question,
        name='questions.unwatch'),
    url(r'^/confirm/(?P<watch_id>\d+)/(?P<secret>\w+)$', views.activate_watch,
        name='questions.activate_watch'),
    url(r'^/unsubscribe/(?P<watch_id>\d+)/(?P<secret>\w+)$',
        views.unsubscribe_watch, name='questions.unsubscribe'),
]
