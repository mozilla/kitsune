from django.conf.urls.defaults import patterns, url, include

from wiki import locale_views


# These patterns inherit (?P<document_slug>[^\/]).
document_patterns = patterns('wiki.views',
    url(r'^$', 'document', name='wiki.document'),
    url(r'^/revision/(?P<revision_id>\d+)$', 'revision',
        name='wiki.revision'),
    url(r'^/history$', 'document_revisions', name='wiki.document_revisions'),
    url(r'^/edit$', 'edit_document', name='wiki.edit_document'),
    url(r'^/edit/(?P<revision_id>\d+)$', 'edit_document',
        name='wiki.new_revision_based_on'),
    url(r'^/review/(?P<revision_id>\d+)$', 'review_revision',
        name='wiki.review_revision'),
    url(r'^/compare$', 'compare_revisions', name='wiki.compare_revisions'),
    url(r'^/translate$', 'translate', name='wiki.translate'),
    url(r'^/readyforl10n/(?P<revision_id>\d+)$',
        'mark_ready_for_l10n_revision',
        name='wiki.mark_ready_for_l10n_revision'),
    url(r'^/locales$', 'select_locale', name='wiki.select_locale'),

    # Un/Subscribe to document edit notifications.
    url(r'^/watch$', 'watch_document', name='wiki.document_watch'),
    url(r'^/unwatch$', 'unwatch_document', name='wiki.document_unwatch'),

    # Vote helpful/not helpful
    url(r'^/vote', 'helpful_vote', name='wiki.document_vote'),

    # Get helpful votes data
    url(r'^/get-votes-async', 'get_helpful_votes_async',
        name="wiki.get_helpful_votes_async"),

    # KB discussion forums
    (r'^/discuss', include('kbforums.urls')),

    # Delete a revision
    url(r'^/revision/(?P<revision_id>\d+)/delete$', 'delete_revision',
        name='wiki.delete_revision'),

    # Delete a document
    url(r'^/delete', 'delete_document', name='wiki.document_delete'),

    # Manage contributors
    url(r'^/add-contributor$', 'add_contributor',
        name='wiki.add_contributor'),
    url(r'^/remove-contributor/(?P<user_id>\d+)$', 'remove_contributor',
        name='wiki.remove_contributor'),

    # Ajax view to indicate a user is ignoring a lock and editing a document.
    url(r'^/steal_lock$', 'steal_lock', name='wiki.steal_lock'),
)

locale_patterns = patterns('wiki.locale_views',
    url(r'^$', 'locale_details', name='wiki.locale_details'),
    url(r'/add-leader$', 'add_leader', name='wiki.add_locale_leader'),
    url(r'^/remove-leader/(?P<user_id>\d+)$', 'remove_leader',
        name='wiki.remove_locale_leader'),
    url(r'/add-reviewer$', 'add_reviewer', name='wiki.add_locale_reviewer'),
    url(r'^/remove-reviewer/(?P<user_id>\d+)$', 'remove_reviewer',
        name='wiki.remove_locale_reviewer'),
    url(r'/add-editor$', 'add_editor', name='wiki.add_locale_editor'),
    url(r'^/remove-editor/(?P<user_id>\d+)$', 'remove_editor',
        name='wiki.remove_locale_editor'),
)

urlpatterns = patterns('wiki.views',
    url(r'^$', 'landing', name='wiki.landing'),

    url(r'^/locales$', locale_views.locale_list, name='wiki.locales'),
    url(r'^/locales/(?P<locale_code>[^/]+)', include(locale_patterns)),

    # (Un)subscribe to locale 'ready for review' notifications.
    url(r'^/watch-ready-for-review$', 'watch_locale',
        name='wiki.locale_watch'),
    url(r'^/unwatch-ready-for-review$', 'unwatch_locale',
        name='wiki.locale_unwatch'),

    # (Un)subscribe to 'approved' notifications.
    url(r'^/watch-approved$', 'watch_approved',
        name='wiki.approved_watch'),
    url(r'^/unwatch-approved$', 'unwatch_approved',
        name='wiki.approved_unwatch'),

    # (Un)subscribe to 'ready-for-l10n' notifications.
    url(r'^/watch-ready$', 'watch_ready',
        name='wiki.ready_watch'),
    url(r'^/unwatch-ready$', 'unwatch_ready',
        name='wiki.ready_unwatch'),

    # Unhelfpul vote survey
    url(r'^/unhelpful-survey', 'unhelpful_survey',
        name='wiki.unhelpful_survey'),

    url(r'^/json$', 'json_view', name='wiki.json'),

    url(r'^/new$', 'new_document', name='wiki.new_document'),
    url(r'^/all$', 'list_documents', name='wiki.all_documents'),
    url(r'^/preview-wiki-content$', 'preview_revision', name='wiki.preview'),
    url(r'^/category/(?P<category>\d+)$', 'list_documents',
        name='wiki.category'),
    url(r'^/topic/(?P<topic>[^/]+)$', 'list_documents', name='wiki.topic'),
    (r'^/(?P<document_slug>[^/]+)', include(document_patterns)),

)

urlpatterns += patterns('kbforums.views',
    # All kb discussions by locale.
    url(r'^/all/discussions$', 'locale_discussions',
        name='wiki.locale_discussions'),

    url(r'^/discuss/watch_locale$', 'watch_locale',
        name='wiki.discuss.watch_locale'),
)
