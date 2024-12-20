from django.urls import include, re_path

from kitsune.kbforums import views as kbforums_views
from kitsune.sumo.views import redirect_to
from kitsune.wiki import locale_views, views
from kitsune.wiki.locale_views import EDITOR, LEADER, REVIEWER

# These patterns inherit (?P<document_slug>[^\/]).
document_patterns = [
    re_path(r"^$", views.document, name="wiki.document"),
    re_path(r"^/revision/(?P<revision_id>\d+)$", views.revision, name="wiki.revision"),
    re_path(r"^/history$", views.document_revisions, name="wiki.document_revisions"),
    re_path(r"^/edit$", views.edit_document, name="wiki.edit_document"),
    re_path(r"^/edit/metadata$", views.edit_document_metadata, name="wiki.edit_document_metadata"),
    re_path(
        r"^/edit/(?P<revision_id>\d+)$", views.edit_document, name="wiki.new_revision_based_on"
    ),
    re_path(r"^/review/(?P<revision_id>\d+)$", views.review_revision, name="wiki.review_revision"),
    re_path(r"^/compare$", views.compare_revisions, name="wiki.compare_revisions"),
    re_path(r"^/translate$", views.translate, name="wiki.translate"),
    re_path(
        r"^/readyforl10n/(?P<revision_id>\d+)$",
        views.mark_ready_for_l10n_revision,
        name="wiki.mark_ready_for_l10n_revision",
    ),
    re_path(r"^/locales$", views.select_locale, name="wiki.select_locale"),
    re_path(r"^/show_translations$", views.show_translations, name="wiki.show_translations"),
    re_path(r"^/links$", views.what_links_here, name="wiki.what_links_here"),
    # Un/Subscribe to document edit notifications.
    re_path(r"^/watch$", views.watch_document, name="wiki.document_watch"),
    re_path(r"^/unwatch$", views.unwatch_document, name="wiki.document_unwatch"),
    # Vote helpful/not helpful
    re_path(r"^/vote", views.handle_vote, name="wiki.document_vote"),
    # Get helpful votes data
    re_path(
        r"^/get-votes-async", views.get_helpful_votes_async, name="wiki.get_helpful_votes_async"
    ),
    # KB discussion forums
    re_path(r"^/discuss/", include("kitsune.kbforums.urls")),
    # Delete a revision
    re_path(
        r"^/revision/(?P<revision_id>\d+)/delete$",
        views.delete_revision,
        name="wiki.delete_revision",
    ),
    # Delete a document
    re_path(r"^/delete", views.delete_document, name="wiki.document_delete"),
    # Manage contributors
    re_path(r"^/add-contributor$", views.add_contributor, name="wiki.add_contributor"),
    re_path(
        r"^/remove-contributor/(?P<user_id>\d+)$",
        views.remove_contributor,
        name="wiki.remove_contributor",
    ),
    # Ajax view to indicate a user is ignoring a lock and editing a document.
    re_path(r"^/steal_lock$", views.steal_lock, name="wiki.steal_lock"),
]

locale_patterns = [
    re_path(r"^$", locale_views.locale_details, name="wiki.locale_details"),
    re_path(
        r"/add-leader$",
        locale_views.add_to_locale,
        {"role": LEADER},
        name="wiki.add_locale_leader",
    ),
    re_path(
        r"^/remove-leader/(?P<user_id>\d+)$",
        locale_views.remove_from_locale,
        {"role": LEADER},
        name="wiki.remove_locale_leader",
    ),
    re_path(
        r"/add-reviewer$",
        locale_views.add_to_locale,
        {"role": REVIEWER},
        name="wiki.add_locale_reviewer",
    ),
    re_path(
        r"^/remove-reviewer/(?P<user_id>\d+)$",
        locale_views.remove_from_locale,
        {"role": REVIEWER},
        name="wiki.remove_locale_reviewer",
    ),
    re_path(
        r"/add-editor$",
        locale_views.add_to_locale,
        {"role": EDITOR},
        name="wiki.add_locale_editor",
    ),
    re_path(
        r"^/remove-editor/(?P<user_id>\d+)$",
        locale_views.remove_from_locale,
        {"role": EDITOR},
        name="wiki.remove_locale_editor",
    ),
]

urlpatterns = [
    re_path(
        r"^$", redirect_to, {"url": "products.product", "slug": "firefox"}, name="wiki.landing"
    ),
    # Redirect for the old how to contribute page.
    re_path(
        r"^/How to contribute$",
        redirect_to,
        {"url": "landings.contribute"},
        name="old_get_involved",
    ),
    re_path(r"^/locales$", locale_views.locale_list, name="wiki.locales"),
    re_path(r"^/locales/(?P<locale_code>[^/]+)/", include(locale_patterns)),
    # (Un)subscribe to locale 'ready for review' notifications.
    re_path(
        r"^/watch-ready-for-review(?:/(?P<product>[^\/]+))?$",
        views.watch_locale,
        name="wiki.locale_watch",
    ),
    re_path(
        r"^/unwatch-ready-for-review(?:/(?P<product>[^\/]+))?$",
        views.unwatch_locale,
        name="wiki.locale_unwatch",
    ),
    # (Un)subscribe to 'approved' notifications.
    re_path(
        r"^/watch-approved(?:/(?P<product>[^\/]+))?$",
        views.watch_approved,
        name="wiki.approved_watch",
    ),
    re_path(
        r"^/unwatch-approved(?:/(?P<product>[^\/]+))?$",
        views.unwatch_approved,
        name="wiki.approved_unwatch",
    ),
    # (Un)subscribe to 'ready-for-l10n' notifications.
    re_path(
        r"^/watch-ready(?:/(?P<product>[^\/]+))?$", views.watch_ready, name="wiki.ready_watch"
    ),
    re_path(
        r"^/unwatch-ready(?:/(?P<product>[^\/]+))?$",
        views.unwatch_ready,
        name="wiki.ready_unwatch",
    ),
    re_path(r"^/json$", views.json_view, name="wiki.json"),
    re_path(r"^/revisions", views.recent_revisions, name="wiki.revisions"),
    re_path(r"^/new$", views.new_document, name="wiki.new_document"),
    re_path(r"^/all$", views.list_documents, name="wiki.all_documents"),
    re_path(r"^/preview-wiki-content$", views.preview_revision, name="wiki.preview"),
    re_path(r"^/save_draft$", views.draft_revision, name="wiki.draft_revision"),
    re_path(r"^/category/(?P<category>\d+)$", views.list_documents, name="wiki.category"),
    re_path(r"^/(?P<document_slug>[^/]+)", include(document_patterns)),
]

urlpatterns += [
    # All kb discussions by locale.
    re_path(
        r"^/all/discussions$", kbforums_views.locale_discussions, name="wiki.locale_discussions"
    ),
    re_path(
        r"^/discuss/watch_locale$", kbforums_views.watch_locale, name="wiki.discuss.watch_locale"
    ),
]

urlpatterns += [
    # Redirect for pocket articles
    # This assumes pocket redirects take the form of:
    # /pocket/<article_id>-<document_slug>
    re_path(
        r"^/pocket/(?:(?P<article_id>\d+)-)?(?P<document_slug>[\w-]+)(?P<extra_path>/[\w/-]*)?/?$",
        views.pocket_article,
        name="wiki.pocket_article",
    ),
]
