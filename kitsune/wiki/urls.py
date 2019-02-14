from django.conf.urls import patterns, url, include

from kitsune.sumo.views import redirect_to
from kitsune.wiki import locale_views
from kitsune.wiki.locale_views import LEADER, REVIEWER, EDITOR


# These patterns inherit (?P<document_slug>[^\/]).
document_patterns = patterns(
    'kitsune.wiki.views',
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
    url(r'^/show_translations$', 'show_translations',
        name='wiki.show_translations'),
    url(r'^/links$', 'what_links_here', name='wiki.what_links_here'),

    # Un/Subscribe to document edit notifications.
    url(r'^/watch$', 'watch_document', name='wiki.document_watch'),
    url(r'^/unwatch$', 'unwatch_document', name='wiki.document_unwatch'),

    # Vote helpful/not helpful
    url(r'^/vote', 'helpful_vote', name='wiki.document_vote'),

    # Get helpful votes data
    url(r'^/get-votes-async', 'get_helpful_votes_async',
        name="wiki.get_helpful_votes_async"),

    # KB discussion forums
    (r'^/discuss', include('kitsune.kbforums.urls')),

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

locale_patterns = patterns(
    'kitsune.wiki.locale_views',
    url(r'^$', 'locale_details', name='wiki.locale_details'),
    url(r'/add-leader$', 'add_to_locale',
        {'role': LEADER}, name='wiki.add_locale_leader'),
    url(r'^/remove-leader/(?P<user_id>\d+)$', 'remove_from_locale',
        {'role': LEADER}, name='wiki.remove_locale_leader'),
    url(r'/add-reviewer$', 'add_to_locale',
        {'role': REVIEWER}, name='wiki.add_locale_reviewer'),
    url(r'^/remove-reviewer/(?P<user_id>\d+)$', 'remove_from_locale',
        {'role': REVIEWER}, name='wiki.remove_locale_reviewer'),
    url(r'/add-editor$', 'add_to_locale',
        {'role': EDITOR}, name='wiki.add_locale_editor'),
    url(r'^/remove-editor/(?P<user_id>\d+)$', 'remove_from_locale',
        {'role': EDITOR}, name='wiki.remove_locale_editor'),
)

urlpatterns = patterns(
    'kitsune.wiki.views',
    url(r'^$', redirect_to,
        {'url': 'products.product', 'slug': 'firefox'}, name='wiki.landing'),

    # Redirect for the old how to contribute page.
    url(r'^/How to contribute$', redirect_to,
        {'url': 'landings.get_involved'}, name='old_get_involved'),

    url(r'^/locales$', locale_views.locale_list, name='wiki.locales'),
    url(r'^/locales/(?P<locale_code>[^/]+)', include(locale_patterns)),

    # (Un)subscribe to locale 'ready for review' notifications.
    url(r'^/watch-ready-for-review(?:/(?P<product>[^\/]+))?$',
        'watch_locale', name='wiki.locale_watch'),
    url(r'^/unwatch-ready-for-review(?:/(?P<product>[^\/]+))?$',
        'unwatch_locale', name='wiki.locale_unwatch'),

    # (Un)subscribe to 'approved' notifications.
    url(r'^/watch-approved(?:/(?P<product>[^\/]+))?$', 'watch_approved',
        name='wiki.approved_watch'),
    url(r'^/unwatch-approved(?:/(?P<product>[^\/]+))?$', 'unwatch_approved',
        name='wiki.approved_unwatch'),

    # (Un)subscribe to 'ready-for-l10n' notifications.
    url(r'^/watch-ready(?:/(?P<product>[^\/]+))?$', 'watch_ready',
        name='wiki.ready_watch'),
    url(r'^/unwatch-ready(?:/(?P<product>[^\/]+))?$', 'unwatch_ready',
        name='wiki.ready_unwatch'),

    # Unhelfpul vote survey
    url(r'^/unhelpful-survey', 'unhelpful_survey',
        name='wiki.unhelpful_survey'),

    url(r'^/json$', 'json_view', name='wiki.json'),
    url(r'^/revisions', 'recent_revisions', name='wiki.revisions'),

    url(r'^/new$', 'new_document', name='wiki.new_document'),
    url(r'^/all$', 'list_documents', name='wiki.all_documents'),
    url(r'^/preview-wiki-content$', 'preview_revision', name='wiki.preview'),
    url(r'^/save_draft$', 'draft_revision', name='wiki.draft_revision'),
    url(r'^/category/(?P<category>\d+)$', 'list_documents',
        name='wiki.category'),
    url(r'^/exp/(?P<document_slug>[^/]+)', 'ux_experiment_view',
        name='wiki.ux_experiment_view'),
    (r'^/(?P<document_slug>[^/]+)', include(document_patterns)),
)

urlpatterns += patterns(
    'kitsune.kbforums.views',
    # All kb discussions by locale.
    url(r'^/all/discussions$', 'locale_discussions',
        name='wiki.locale_discussions'),

    url(r'^/discuss/watch_locale$', 'watch_locale',
        name='wiki.discuss.watch_locale'),
)
