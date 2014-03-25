from django.conf.urls import patterns, url
from django.contrib.contenttypes.models import ContentType

from kitsune.questions.feeds import (
    QuestionsFeed, AnswersFeed, TaggedQuestionsFeed)
from kitsune.questions.models import Question, Answer
from kitsune.flagit import views as flagit_views


urlpatterns = patterns(
    'kitsune.questions.views',
    url(r'^$', 'product_list', name='questions.home'),

    url(r'^/answer-preview-async$', 'answer_preview_async',
        name='questions.answer_preview_async'),
    url(r'^/dashboard/metrics$', 'metrics', name='questions.metrics'),
    url(r'^/dashboard/metrics/(?P<locale_code>[^/]+)$', 'metrics',
        name='questions.locale_metrics'),

    # AAQ
    url(r'^/new$', 'aaq', name='questions.aaq_step1'),
    url(r'^/new/confirm$', 'aaq_confirm', name='questions.aaq_confirm'),
    url(r'^/new/(?P<product_key>[\w\-]+)$',
        'aaq_step2', name='questions.aaq_step2'),
    url(r'^/new/(?P<product_key>[\w\-]+)/(?P<category_key>[\w\-]+)$',
        'aaq_step3', name='questions.aaq_step3'),
    url(r'^/new/(?P<product_key>[\w\-]+)/(?P<category_key>[\w\-]+)/search$',
        'aaq_step4', name='questions.aaq_step4'),
    url(r'^/new/(?P<product_key>[\w\-]+)/(?P<category_key>[\w\-]+)/form$',
        'aaq_step5', name='questions.aaq_step5'),

    # AAQ flow for Marketplace
    url(r'^/marketplace$', 'marketplace', name='questions.marketplace_aaq'),
    url(r'^/marketplace/success$',
        'marketplace_success', name='questions.marketplace_aaq_success'),
    url(r'^/marketplace/refund$', 'marketplace_refund',
        name='questions.marketplace_refund'),
    url(r'^/marketplace/developer-request$', 'marketplace_developer_request',
        name='questions.marketplace_developer_request'),
    url(r'^/marketplace/(?P<category_slug>[\w\-]+)$',
        'marketplace_category', name='questions.marketplace_aaq_category'),

    # TODO: Factor out `/(?P<question_id>\d+)` below
    url(r'^/(?P<question_id>\d+)$', 'question_details', name='questions.details'),
    url(r'^/(?P<question_id>\d+)/edit$',
        'edit_question', name='questions.edit_question'),
    url(r'^/(?P<question_id>\d+)/edit-details$',
        'edit_details', name='questions.edit_details'),
    url(r'^/(?P<question_id>\d+)/reply$', 'reply', name='questions.reply'),
    url(r'^/(?P<question_id>\d+)/delete$', 'delete_question',
        name='questions.delete'),
    url(r'^/(?P<question_id>\d+)/lock$', 'lock_question',
        name='questions.lock'),
    url(r'^/(?P<question_id>\d+)/archive$', 'archive_question',
        name='questions.archive'),
    url(r'^/(?P<question_id>\d+)/delete/(?P<answer_id>\d+)$',
        'delete_answer', name='questions.delete_answer'),
    url(r'^/(?P<question_id>\d+)/edit/(?P<answer_id>\d+)$', 'edit_answer',
        name='questions.edit_answer'),
    url(r'^/(?P<question_id>\d+)/solve/(?P<answer_id>\d+)$', 'solve',
        name='questions.solve'),
    url(r'^/(?P<question_id>\d+)/unsolve/(?P<answer_id>\d+)$', 'unsolve',
        name='questions.unsolve'),
    url(r'^/(?P<question_id>\d+)/vote$', 'question_vote',
        name='questions.vote'),
    url(r'^/(?P<question_id>\d+)/vote/(?P<answer_id>\d+)$',
        'answer_vote', name='questions.answer_vote'),
    url(r'^/(?P<question_id>\d+)/add-tag$', 'add_tag',
        name='questions.add_tag'),
    url(r'^/(?P<question_id>\d+)/remove-tag$', 'remove_tag',
        name='questions.remove_tag'),
    url(r'^/(?P<question_id>\d+)/add-tag-async$', 'add_tag_async',
        name='questions.add_tag_async'),
    url(r'^/(?P<question_id>\d+)/remove-tag-async$', 'remove_tag_async',
        name='questions.remove_tag_async'),

    # Question lists
    url(r'^/(?P<product_slug>[\w+\-]+)$', 'question_list',
        name='questions.list'),

    # Flag content ("Report this post")
    url(r'^/(?P<object_id>\d+)/flag$', flagit_views.flag,
        {'content_type': ContentType.objects.get_for_model(Question).id},
        name='questions.flag'),
    url(r'^/(?P<question_id>\d+)/flag/(?P<object_id>\d+)$', flagit_views.flag,
        {'content_type': ContentType.objects.get_for_model(Answer).id},
        name='questions.answer_flag'),

    # Subcribe by email
    url(r'^/(?P<question_id>\d+)/watch$', 'watch_question',
        name='questions.watch'),
    url(r'^/(?P<question_id>\d+)/unwatch$', 'unwatch_question',
        name='questions.unwatch'),
    url(r'^/confirm/(?P<watch_id>\d+)/(?P<secret>\w+)$', 'activate_watch',
        name='questions.activate_watch'),
    url(r'^/unsubscribe/(?P<watch_id>\d+)/(?P<secret>\w+)$',
        'unsubscribe_watch', name='questions.unsubscribe'),

    # Feeds
    url(r'^/feed$', QuestionsFeed(), name='questions.feed'),
    url(r'^/(?P<question_id>\d+)/feed$', AnswersFeed(),
        name='questions.answers.feed'),
    url(r'^/tagged/(?P<tag_slug>[\w\-]+)/feed$', TaggedQuestionsFeed(),
        name='questions.tagged_feed'),
)
