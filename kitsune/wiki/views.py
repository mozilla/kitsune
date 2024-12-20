import json
import logging
import time
from datetime import datetime
from datetime import time as datetime_time
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, OuterRef, Q
from django.db.models.functions import Now, TruncDate
from django.forms.utils import ErrorList
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.cache import patch_vary_headers
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation.trans_real import parse_accept_lang_header
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from kitsune.access.decorators import login_required
from kitsune.lib.sumo_locales import LOCALES
from kitsune.products.models import Product, Topic
from kitsune.products.views import product_landing
from kitsune.sumo.decorators import ratelimit
from kitsune.sumo.i18n import normalize_language
from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import (
    get_next_url,
    paginate,
    set_aaq_context,
    smart_int,
    truncated_json_dumps,
)
from kitsune.wiki.config import (
    CATEGORIES,
    COLLAPSIBLE_DOCUMENTS,
    DOCUMENTS_PER_PAGE,
    FALLBACK_LOCALES,
    MAJOR_SIGNIFICANCE,
    TEMPLATES_CATEGORY,
)
from kitsune.wiki.events import (
    ApprovedOrReadyUnion,
    ApproveRevisionInLocaleEvent,
    EditDocumentEvent,
    ReadyRevisionEvent,
    ReviewableRevisionInLocaleEvent,
)
from kitsune.wiki.facets import topics_for
from kitsune.wiki.forms import (
    AddContributorForm,
    DocumentForm,
    DraftRevisionForm,
    ReviewForm,
    RevisionFilterForm,
    RevisionForm,
)
from kitsune.wiki.models import (
    Document,
    DraftRevision,
    HelpfulVote,
    ImportantDate,
    Revision,
    SlugCollision,
    TitleCollision,
    doc_html_cache_key,
)
from kitsune.wiki.parser import wiki_to_html
from kitsune.wiki.tasks import (
    render_document_cascade,
    schedule_rebuild_kb,
    send_contributor_notification,
    send_reviewed_notification,
)
from kitsune.wiki.utils import get_visible_document_or_404, get_visible_revision_or_404

log = logging.getLogger("k.wiki")


def doc_page_cache(view):
    """Decorator that caches the document page HTML."""

    @wraps(view)
    def _doc_page_cache_view(request, document_slug, *args, **kwargs):
        # We skip caching for authed users or if redirect=no
        # is in the query string or if we show the aaq widget
        if (
            request.user.is_authenticated
            or request.GET.get("redirect") == "no"
            or request.session.get("product_slug")
            or settings.DEV
        ):
            return view(request, document_slug, *args, **kwargs)

        cache_key = doc_html_cache_key(locale=request.LANGUAGE_CODE, slug=document_slug)

        html, headers = cache.get(cache_key, (None, None))
        if html is not None:
            res = HttpResponse(html)
            for key, val in list(headers.items()):
                res[key] = val
            return res

        response = view(request, document_slug, *args, **kwargs)

        # We only cache if the response returns HTTP 200 and depends
        # only on the URL, not anything in the request headers.
        if (response.status_code == 200) and ("vary" not in response):
            cache.set(cache_key, (response.content, dict(list(response.headers.items()))))

        return response

    return _doc_page_cache_view


@require_GET
@doc_page_cache
def document(request, document_slug, document=None):
    """View a wiki document."""

    fallback_reason = None
    full_locale_name = None
    vary_on_accept_language = False

    def maybe_vary_on_accept_language(response):
        """
        Patch the VARY header in the response to include "Accept-Language"
        if the Accept-Language header could vary the response, and return
        the response.
        """
        if vary_on_accept_language:
            patch_vary_headers(response, ["accept-language"])
        return response

    doc = get_visible_document_or_404(
        request.user,
        locale=request.LANGUAGE_CODE,
        slug=document_slug,
        look_for_translation_via_parent=True,
        return_parent_if_no_translation=True,
    )

    if doc.slug != document_slug:
        # We've found the translation at a different slug.
        url = doc.get_absolute_url()
        url = urlparams(url, query_dict=request.GET)
        return HttpResponseRedirect(url)

    if doc.locale != request.LANGUAGE_CODE:
        # The "doc" is the parent document.
        if doc.current_revision:
            # Check for unapproved revisions
            unapproved_translation_exists = Revision.objects.filter(
                is_approved=False,
                document__parent=doc,
                document__locale=request.LANGUAGE_CODE,
            ).exists()
            if unapproved_translation_exists:
                fallback_reason = "translation_not_approved"
            else:
                # There is no translation, so we'll fall back to its approved parent,
                # unless we find an approved translation in a fallback locale.
                fallback_reason = "no_translation"

                # Find and show the defined fallback locale rather than the English
                # version of the document. The fallback locale is defined based on
                # the ACCEPT_LANGUAGE header, site-wide locale mapping and custom
                # fallback locale. The custom fallback locale is defined in the
                # FALLBACK_LOCALES array in kitsune/wiki/config.py. See bug 800880
                # for more details
                fallback_locale, vary_on_accept_language = get_fallback_locale(doc, request)

                # If a fallback locale is defined, show the document in that locale,
                # otherwise continue with the document in the default language.
                if fallback_locale:
                    # If we have a fallback locale, it means we're guaranteed to have
                    # a translation in that locale with approved content.
                    doc = doc.translated_to(fallback_locale)
                    # For showing the fallback locale explanation message to the user
                    fallback_reason = "fallback_locale"
                    full_locale_name = {
                        request.LANGUAGE_CODE: LOCALES[request.LANGUAGE_CODE].native,
                        fallback_locale: LOCALES[fallback_locale].native,
                    }

    if not doc.current_revision:
        # We've got a document, but it has no approved content.
        if doc.parent and doc.parent.current_revision:
            # The "doc" is a translation with no approved content, but its
            # parent has approved content, so let's fall back to its parent.
            fallback_reason = "translation_not_approved"
        else:
            # We can't find any approved content to show.
            fallback_reason = "no_content"

    any_localizable_revision = doc.revisions.filter(
        is_approved=True, is_ready_for_localization=True
    ).exists()
    # Obey explicit redirect pages:
    # Don't redirect on redirect=no (like Wikipedia), so we can link from a
    # redirected-to-page back to a "Redirected from..." link, so you can edit
    # the redirect.
    redirect_url = (
        None if request.GET.get("redirect") == "no" else doc.redirect_url(request.LANGUAGE_CODE)
    )
    if redirect_url:
        url = urlparams(
            redirect_url, query_dict=request.GET, redirectslug=doc.slug, redirectlocale=doc.locale
        )
        return maybe_vary_on_accept_language(HttpResponseRedirect(url))

    # Get "redirected from" doc if we were redirected:
    redirect_slug = request.GET.get("redirectslug")
    redirect_locale = request.GET.get("redirectlocale")
    redirected_from = None
    if redirect_slug and redirect_locale:
        try:
            redirected_from = Document.objects.get_visible(
                request.user, locale=redirect_locale, slug=redirect_slug
            )
        except Document.DoesNotExist:
            pass

    contributors = doc.contributors.all()

    products = doc.get_products()
    if len(products) < 1:
        product = Product.active.filter(visible=True)[0]
    else:
        product = products.first()

    # Set the AAQ context for the widget
    set_aaq_context(request, product)

    product_topics = Topic.active.filter(products=product, visible=True)

    # Create serialized versions of the document's associated products and topics
    # to be used within GA as parameters/dimensions.
    ga_products = f"/{'/'.join(products.order_by('slug').values_list('slug', flat=True))}/"
    ga_topics = f"/{'/'.join(doc.get_topics().order_by('slug').values_list('slug', flat=True))}/"
    # Provide the actual locale of the document that will also be used as a GA parameter/dimension.
    ga_article_locale = (
        doc.parent.locale
        if (fallback_reason == "translation_not_approved") and doc.parent
        else doc.locale
    )

    # Switching devices section
    switching_devices_product = switching_devices_topic = switching_devices_subtopics = None
    if doc.is_switching_devices_document:
        # make sure that the article is in the right product and topic
        if (
            not products.filter(slug="firefox").exists()
            or not product_topics.filter(slug=settings.FIREFOX_SWITCHING_DEVICES_TOPIC).exists()
        ):
            raise Http404

        switching_devices_product = Product.active.get(slug="firefox")
        switching_devices_topic = Topic.active.get(
            products=switching_devices_product, slug=settings.FIREFOX_SWITCHING_DEVICES_TOPIC
        )
        switching_devices_subtopics = topics_for(
            request.user, product=switching_devices_product, parent=switching_devices_topic
        )

    if document_slug in COLLAPSIBLE_DOCUMENTS.get(request.LANGUAGE_CODE, []):
        document_css_class = "collapsible"
    else:
        document_css_class = ""

    # Build a set of breadcrumbs, ending with the document's title, and
    # starting with the product, with the topic(s) in between.
    # The breadcrumbs are built backwards, and then reversed.

    # Get document title. If it is like "Title - Subtitle", strip off the subtitle.
    trimmed_title = doc.title.split(" - ")[0].strip()
    breadcrumbs = [(None, trimmed_title)]
    # Get the dominant topic, and all parent topics. Save the topic chosen for
    # picking a product later.
    document_topics = doc.topics.order_by("display_order")
    if len(document_topics) > 0:
        topic = document_topics.first()
        breadcrumbs.append((topic.get_absolute_url(product.slug), topic.title))
    breadcrumbs.append((product.get_absolute_url(), product.title))
    # The list above was built backwards, so flip this.
    breadcrumbs.reverse()
    votes = HelpfulVote.objects.filter(revision=doc.current_revision).aggregate(
        total_votes=Count("id"),
        helpful_votes=Count("id", filter=Q(helpful=True)),
    )
    helpful_votes = (
        int((votes["helpful_votes"] / votes["total_votes"]) * 100)
        if votes["total_votes"] > 0
        else 0
    )

    is_first_revision = doc.revisions.filter(is_approved=True).count() == 1

    data = {
        "document": doc,
        "is_first_revision": is_first_revision,
        "redirected_from": redirected_from,
        "contributors": contributors,
        "fallback_reason": fallback_reason,
        "helpful_votes": helpful_votes,
        "product_topics": product_topics,
        "product": product,
        "products": products,
        "ga_topics": ga_topics,
        "ga_products": ga_products,
        "ga_article_locale": ga_article_locale,
        "related_products": doc.related_products.exclude(pk=product.pk),
        "breadcrumb_items": breadcrumbs,
        "document_css_class": document_css_class,
        "any_localizable_revision": any_localizable_revision,
        "full_locale_name": full_locale_name,
        "switching_devices_product": switching_devices_product,
        "switching_devices_topic": switching_devices_topic,
        "switching_devices_subtopics": switching_devices_subtopics,
        "product_titles": ", ".join(p.title for p in sorted(products, key=lambda p: p.title)),
    }

    return maybe_vary_on_accept_language(render(request, "wiki/document.html", data))


def revision(request, document_slug, revision_id):
    """View a wiki document revision."""
    rev = get_visible_revision_or_404(
        request.user,
        pk=revision_id,
        document__slug=document_slug,
        document__locale=request.LANGUAGE_CODE,
    )
    doc = rev.document
    data = {"document": doc, "revision": rev}
    return render(request, "wiki/revision.html", data)


@require_GET
def list_documents(request, category=None):
    """List wiki documents."""
    user = request.user
    docs = Document.objects.visible(user, locale=request.LANGUAGE_CODE).order_by("title")

    if category:
        docs = docs.filter(category=category)
        try:
            category_id = int(category)
        except ValueError:
            raise Http404
        try:
            category = str(dict(CATEGORIES)[category_id])
        except KeyError:
            raise Http404
    docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)

    return render(request, "wiki/list_documents.html", {"documents": docs, "category": category})


@login_required
def new_document(request):
    """Create a new wiki document."""
    products = Product.active.filter(visible=True)
    if request.method == "GET":
        doc_form = DocumentForm(initial_title=request.GET.get("title"))
        rev_form = RevisionForm()
        return render(
            request,
            "wiki/new_document.html",
            {
                "document_form": doc_form,
                "revision_form": rev_form,
                "products": products,
            },
        )

    post_data = request.POST.copy()
    post_data.update({"locale": request.LANGUAGE_CODE})
    doc_form = DocumentForm(post_data)
    rev_form = RevisionForm(post_data)

    if doc_form.is_valid() and rev_form.is_valid():
        doc = doc_form.save(None)
        _save_rev_and_notify(rev_form, request.user, doc)
        return HttpResponseRedirect(reverse("wiki.document_revisions", args=[doc.slug]))

    return render(
        request,
        "wiki/new_document.html",
        {
            "document_form": doc_form,
            "revision_form": rev_form,
            "products": products,
        },
    )


_document_lock_key = "sumo::wiki::document::{id}::lock"


def _document_lock_check(document_id):
    """Check for a lock on a document.

    Returns the username of the user that has the page locked, or ``None`` if
    no user has a lock.
    """
    try:
        redis = redis_client(name="default")
        key = _document_lock_key.format(id=document_id)
        return redis.get(key)
    except RedisError as e:
        log.error("Redis error: %s" % e)
        return None


def _document_lock_steal(document_id, user_name, expire_time=60 * 15):
    """Lock a document for a user.

    Note that this does not check if the page is already locked, and simply
    sets the lock on the page.
    """
    try:
        redis = redis_client(name="default")
        key = _document_lock_key.format(id=document_id)
        it_worked = redis.set(key, user_name)
        redis.expire(key, expire_time)
        return it_worked
    except RedisError as e:
        log.error("Redis error: %s" % e)
        return False


def _document_lock_clear(document_id, user_name):
    """Remove a lock from a document.

    This would be used to indicate the given user no longer wants the page
    locked, so the lock should be cleared.

    If the `user` parameter does not match the current lock, the lock remains
    in place.

    Returns true if the lock was removed, false otherwise.
    """
    try:
        redis = redis_client(name="default")
        key = _document_lock_key.format(id=document_id)
        locked_by = redis.get(key)
        if locked_by == user_name:
            return redis.delete(key)
        else:
            return False
    except RedisError as e:
        log.error("Redis error: %s" % e)
        return False


def _document_lock(doc_id, username):
    """If there is no lock, take one. Return the current state of the lock."""
    locked_by = _document_lock_check(doc_id)
    if locked_by == username:
        locked = False
    if locked_by:
        try:
            locked = not (locked_by == username)
            locked_by = User.objects.get(username=locked_by)
        except User.DoesNotExist:
            # If the user doesn't exist, they can't take a lock.
            locked = False
            locked_by = None
    else:
        locked_by = username
        locked = False
        _document_lock_steal(doc_id, username)

    return locked, locked_by


@login_required
@require_http_methods(["POST"])
def steal_lock(request, document_slug, revision_id=None):
    user = request.user
    doc = get_visible_document_or_404(user, locale=request.LANGUAGE_CODE, slug=document_slug)
    ok = _document_lock_steal(doc.id, user.username)
    return HttpResponse("", status=200 if ok else 400)


def edit_init_and_perms(request, document_slug, revision_id=None, doctype="doc"):
    user = request.user
    doc = get_visible_document_or_404(
        user,
        locale=request.LANGUAGE_CODE,
        slug=document_slug,
        look_for_translation_via_parent=True,
        return_parent_if_no_translation=True,
    )

    if doctype == "doc":
        if not doc.allows(user, "create_revision"):
            raise PermissionDenied
    if doctype == "meta":
        if not doc.allows(user, "edit"):
            raise PermissionDenied

    if doc.locale != request.LANGUAGE_CODE:
        # We've fallen back to the parent, since no visible translation existed.
        url = reverse("wiki.translate", locale=request.LANGUAGE_CODE, args=[document_slug])
        return HttpResponseRedirect(url)

    # If this document has a parent, then the edit is handled by the
    # translate view. Pass it on.
    if doc.parent:
        return translate(request, doc.parent.slug, revision_id)

    if revision_id:
        rev = get_object_or_404(Revision, pk=revision_id, document=doc)
    else:
        rev = doc.current_revision or doc.revisions.order_by("-created", "-id")[0]

    return user, doc, rev


@require_http_methods(["GET", "POST"])
@login_required
def edit_document(request, document_slug, revision_id=None):
    """Create a new revision of a wiki document"""

    # Initialize values and check basic perms
    init_check = edit_init_and_perms(request, document_slug, revision_id, "doc")
    # If we were redirected during init, return that response.
    if isinstance(init_check, HttpResponse):
        return init_check
    user, doc, rev = init_check

    rev_form = RevisionForm(instance=rev, initial={"based_on": rev.id, "comment": ""})

    # POST
    if request.method == "POST":
        rev_form = RevisionForm(request.POST)
        rev_form.instance.document = doc  # for rev_form.clean()
        if rev_form.is_valid():
            _document_lock_clear(doc.id, user.username)
            _save_rev_and_notify(rev_form, user, doc, base_rev=rev)
            if "notify-future-changes" in request.POST:
                EditDocumentEvent.notify(request.user, doc)
            return HttpResponseRedirect(reverse("wiki.document_revisions", args=[document_slug]))

    show_revision_warning = _show_revision_warning(doc, rev)
    locked, locked_by = _document_lock(doc.id, user.username)

    return render(
        request,
        "wiki/edit.html",
        {
            "revision_form": rev_form,
            "document": doc,
            "show_revision_warning": show_revision_warning,
            "locked": locked,
            "locked_by": locked_by,
        },
    )


@require_http_methods(["GET", "POST"])
@login_required
def edit_document_metadata(request, document_slug, revision_id=None):
    """Edit document metadata."""

    # Initialize values and check basic perms
    init_check = edit_init_and_perms(request, document_slug, revision_id, "meta")
    # If we were redirected, return that response.
    if isinstance(init_check, HttpResponse):
        return init_check
    user, doc, rev = init_check

    can_edit_needs_change = doc.allows(user, "edit_needs_change")
    can_archive = doc.allows(user, "archive")

    doc_form = DocumentForm(
        initial=_document_form_initial(doc),
        can_archive=can_archive,
        can_edit_needs_change=can_edit_needs_change,
    )

    if request.method == "POST":  # POST
        _document_lock_clear(doc.id, user.username)

        post_data = request.POST.copy()
        post_data.update({"locale": request.LANGUAGE_CODE})

        doc_form = DocumentForm(
            post_data,
            instance=doc,
            can_archive=can_archive,
            can_edit_needs_change=can_edit_needs_change,
        )
        if doc_form.is_valid():
            # Get the possibly new slug for the imminent redirection:
            try:
                doc = doc_form.save(None)
            except (TitleCollision, SlugCollision) as metadata_error:
                errors = doc_form._errors.setdefault("title", ErrorList())
                message = "The {type} you selected is already in use."
                message = message.format(
                    type="title" if isinstance(metadata_error, TitleCollision) else "slug"
                )
                errors.append(_(message))
            else:
                # Do we need to rebuild the KB?
                _maybe_schedule_rebuild(doc_form)
                return HttpResponseRedirect(reverse("wiki.document", args=[doc.slug]))

    show_revision_warning = _show_revision_warning(doc, rev)
    locked, locked_by = _document_lock(doc.id, user.username)

    return render(
        request,
        "wiki/edit_metadata.html",
        {
            "document_form": doc_form,
            "document": doc,
            "show_revision_warning": show_revision_warning,
            "locked": locked,
            "locked_by": locked_by,
        },
    )


@login_required
@require_POST
def draft_revision(request):
    """Create a Draft Revision.

    User can have only one draft revision for a translated document. Store the draft with
    parent document, user and locale. Get the parent document from the based on revision"""
    draft_form = DraftRevisionForm(request.POST)
    if draft_form.is_valid():
        draft_form.save(request=request)
        return HttpResponse(status=201)

    return HttpResponseBadRequest()


@login_required
@require_POST
def preview_revision(request):
    """Create an HTML fragment preview of the posted wiki syntax."""
    wiki_content = request.POST.get("content", "")
    slug = request.POST.get("slug")
    locale = request.POST.get("locale")

    if slug and locale:
        doc = get_visible_document_or_404(request.user, locale=locale, slug=slug)
        products = doc.get_products()
    else:
        products = Product.active.all()

    data = {"content": wiki_to_html(wiki_content, request.LANGUAGE_CODE), "products": products}
    return render(request, "wiki/preview.html", data)


@require_GET
def document_revisions(request, document_slug, contributor_form=None):
    """List all the revisions of a given document."""
    locale = request.GET.get("locale", request.LANGUAGE_CODE)

    doc = get_visible_document_or_404(
        request.user,
        locale=locale,
        slug=document_slug,
        look_for_translation_via_parent=True,
    )

    if doc.slug != document_slug:
        # We've found the translation at a different slug.
        url = reverse("wiki.document_revisions", args=[doc.slug], locale=locale)
        return HttpResponseRedirect(url)

    revs = Revision.objects.filter(document=doc).order_by("-created", "-id")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        template = "wiki/includes/revision_list.html"
    else:
        template = "wiki/history.html"

    form = contributor_form or AddContributorForm()
    return render(
        request, template, {"revisions": revs, "document": doc, "contributor_form": form}
    )


@login_required
def review_revision(request, document_slug, revision_id):
    """Review a revision of a wiki document."""
    rev = get_visible_revision_or_404(
        request.user,
        pk=revision_id,
        document__slug=document_slug,
        document__locale=request.LANGUAGE_CODE,
    )
    doc = rev.document

    if not doc.allows(request.user, "review_revision"):
        raise PermissionDenied

    form = ReviewForm(
        initial={
            "needs_change": doc.needs_change,
            "needs_change_comment": doc.needs_change_comment,
        }
    )

    # Don't ask significance if this doc is a translation or if it has no
    # former approved versions:
    should_ask_significance = not doc.parent and doc.current_revision

    based_on_revs = doc.revisions.all()
    last_approved_date = getattr(doc.current_revision, "created", datetime.fromordinal(1))
    based_on_revs = based_on_revs.filter(created__gt=last_approved_date)
    revision_contributors = list(set(based_on_revs.values_list("creator__username", flat=True)))

    # Get Unreviewed Revisions
    unreviewed_revisions = Revision.objects.filter(
        document=doc, is_approved=False, reviewed=None
    ).order_by("-id")

    # Get latest revision which is still not approved. Use **latest_revision_id** to get the id.
    try:
        latest_unapproved_revision = unreviewed_revisions[0]
        latest_unapproved_revision_id = latest_unapproved_revision.id
    except IndexError:
        latest_unapproved_revision_id = None

    # Get Current Revision id only if there is any approved revision.
    # Return None if there is no current revision
    if doc.current_revision is not None:
        current_revision_id = doc.current_revision.id
        unreviewed_revisions = unreviewed_revisions.exclude(id__lt=current_revision_id)
    else:
        current_revision_id = None

    # Get latest 5 unapproved revisions and exclude the revision which is being reviewed
    unreviewed_revisions = unreviewed_revisions.exclude(id=rev.id)[:5]

    # Don't include the reviewer in the recent contributors list.
    if request.user.username in revision_contributors:
        revision_contributors.remove(request.user.username)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid() and not rev.reviewed:
            # Don't allow revisions to be reviewed twice
            rev.is_approved = "approve" in request.POST
            rev.reviewer = request.user
            rev.reviewed = datetime.now()

            if should_ask_significance and form.cleaned_data["significance"]:
                rev.significance = form.cleaned_data["significance"]
            elif not should_ask_significance and not doc.parent:
                # This is a new document without approved revisions.
                # Significance is MAJOR.
                rev.significance = MAJOR_SIGNIFICANCE

            # If document is localizable and revision was approved and
            # user has permission, set the is_ready_for_localization value.
            if (
                doc.allows(request.user, "mark_ready_for_l10n")
                and rev.is_approved
                and rev.can_be_readied_for_localization()
            ):
                rev.is_ready_for_localization = form.cleaned_data["is_ready_for_localization"]

                # If the revision is ready for l10n, store the date
                # and the user.
                if rev.is_ready_for_localization:
                    rev.readied_for_localization = rev.reviewed
                    rev.readied_for_localization_by = rev.reviewer

            rev.save()

            # Update the needs change bit (if approved, default language and
            # user has permission).
            if (
                doc.locale == settings.WIKI_DEFAULT_LANGUAGE
                and doc.allows(request.user, "edit_needs_change")
                and rev.is_approved
            ):
                doc.needs_change = form.cleaned_data["needs_change"]

                # Remove comment if no changes are needed.
                if doc.needs_change:
                    doc.needs_change_comment = form.cleaned_data["needs_change_comment"]
                else:
                    doc.needs_change_comment = ""

                doc.save()

            # Send notifications of approvedness and readiness:
            if rev.is_ready_for_localization or rev.is_approved:
                ApprovedOrReadyUnion(rev).fire(exclude=[rev.creator, request.user])

            # Send an email (not really a "notification" in the sense that
            # there's a Watch table entry) to revision creator.
            msg = form.cleaned_data["comment"]
            send_reviewed_notification.delay(rev.id, doc.id, msg)
            based_on_revs_ids = based_on_revs.values_list("id", flat=True)
            send_contributor_notification(based_on_revs_ids, rev.id, doc.id, msg)

            render_document_cascade.delay(doc.id)

            return HttpResponseRedirect(reverse("wiki.document_revisions", args=[document_slug]))

    if doc.parent:  # A translation
        # For diffing the based_on revision against, to help the user see if he
        # translated all the recent changes:
        parent_revision = rev.based_on or doc.parent.localizable_or_latest_revision()
        template = "wiki/review_translation.html"
    else:
        parent_revision = None
        template = "wiki/review_revision.html"

    data = {
        "revision": rev,
        "document": doc,
        "form": form,
        "parent_revision": parent_revision,
        "revision_contributors": list(revision_contributors),
        "should_ask_significance": should_ask_significance,
        "latest_unapproved_revision_id": latest_unapproved_revision_id,
        "current_revision_id": current_revision_id,
        "unreviewed_revisions": unreviewed_revisions,
    }
    return render(request, template, data)


@require_GET
def compare_revisions(request, document_slug):
    """Compare two wiki document revisions.

    The ids are passed as query string parameters (to and from).

    """
    locale = request.GET.get("locale", request.LANGUAGE_CODE)
    doc = get_visible_document_or_404(request.user, locale=locale, slug=document_slug)
    if "from" not in request.GET or "to" not in request.GET:
        raise Http404

    from_id = smart_int(request.GET.get("from"))
    to_id = smart_int(request.GET.get("to"))
    revision_from = get_object_or_404(Revision, document=doc, id=from_id)
    revision_to = get_object_or_404(Revision, document=doc, id=to_id)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        template = "wiki/includes/revision_diff.html"
    else:
        template = "wiki/compare_revisions.html"

    return render(
        request,
        template,
        {"document": doc, "revision_from": revision_from, "revision_to": revision_to},
    )


@login_required
def select_locale(request, document_slug):
    """Select a locale to translate the document to."""
    doc = get_visible_document_or_404(
        request.user, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug
    )
    translated_locales_code = []  # Translated Locales list with Locale Code only
    translated_locales = []
    untranslated_locales = []

    translated_locales_code.append(doc.locale)
    translated_locales_code.extend(doc.translations.all().values_list("locale", flat=True))

    # Finding out the Translated and Untranslated locales with Locale Name and Locale Code
    for locale in settings.LANGUAGE_CHOICES:
        if locale[0] in translated_locales_code:
            translated_locales.append(locale)
        else:
            untranslated_locales.append(locale)

    return render(
        request,
        "wiki/select_locale.html",
        {
            "document": doc,
            "translated_locales": translated_locales,
            "untranslated_locales": untranslated_locales,
        },
    )


@login_required
def translate(request, document_slug, revision_id=None):
    """Create a new translation of a wiki document.

    * document_slug is for the default locale
    * translation is to the request.LANGUAGE_CODE

    """

    # Inialization and checks
    user = request.user
    parent_doc = get_visible_document_or_404(
        user, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug
    )

    if settings.WIKI_DEFAULT_LANGUAGE == request.LANGUAGE_CODE:
        # Don't translate to the default language.
        return HttpResponseRedirect(
            reverse(
                "wiki.edit_document", locale=settings.WIKI_DEFAULT_LANGUAGE, args=[parent_doc.slug]
            )
        )

    if not parent_doc.is_localizable:
        message = _lazy("You cannot translate this document.")
        return render(request, "handlers/400.html", {"message": message}, status=400)

    based_on_rev = parent_doc.localizable_or_latest_revision(include_rejected=True)

    disclose_description = bool(request.GET.get("opendescription"))

    try:
        doc = parent_doc.translations.get(locale=request.LANGUAGE_CODE)
    except Document.DoesNotExist:
        doc = None
        disclose_description = True
    else:
        if not doc.is_visible_for(user):
            # A translation has been started, but isn't approved yet for
            # public visibility, and this user doesn't have permission
            # to see/work on it.
            raise PermissionDenied

    user_has_doc_perm = not doc or doc.allows(user, "edit")
    user_has_rev_perm = not doc or doc.allows(user, "create_revision")

    if not user_has_doc_perm and not user_has_rev_perm:
        # User has no perms, bye.
        raise PermissionDenied

    # Check if the user has draft revision saved for the parent document with requeted locale
    draft = DraftRevision.objects.filter(
        creator=user, document=parent_doc, locale=request.LANGUAGE_CODE
    ).first()

    base_rev = doc_form = rev_form = None

    if user_has_doc_perm:
        # Restore draft if draft is available and user requested to restore
        doc_initial = _document_form_initial(doc) if doc else {}
        doc_form = DocumentForm(initial=doc_initial)

    if user_has_rev_perm:
        rev_initial = {"based_on": based_on_rev.id, "comment": ""}

        if revision_id:
            base_rev = Revision.objects.get(pk=revision_id)
            rev_initial.update(
                content=base_rev.content, summary=base_rev.summary, keywords=base_rev.keywords
            )
        elif not doc:
            rev_initial.update(
                content=based_on_rev.content,
                summary=based_on_rev.summary,
                keywords=based_on_rev.keywords,
            )

        # Get a revision of the translation to plonk into the page as a
        # starting point. Since translations are never "ready for
        # localization", this will first try to find an approved revision, then
        # an unrejected one, then give up.
        instance = doc and doc.localizable_or_latest_revision()

        rev_form = RevisionForm(instance=instance, initial=rev_initial)
        base_rev = base_rev or instance

    if request.method == "POST":
        # Use POST for restoring and deleting drafts to avoid CSRF
        restore_draft = "restore" in request.POST and bool(draft)
        discard_draft = "discard" in request.POST and bool(draft)
        # Make sure that one of the two is True but not both
        if discard_draft ^ restore_draft:
            if discard_draft:
                draft.delete()
                return HttpResponseRedirect(
                    urlparams(reverse("wiki.translate", args=[document_slug]))
                )

            # If we are here - we have a draft to restore
            if user_has_doc_perm:
                doc_initial.update({"title": draft.title, "slug": draft.slug})
                doc_form = DocumentForm(initial=doc_initial)
            if user_has_rev_perm:
                rev_initial.update(
                    {
                        "content": draft.content,
                        "summary": draft.summary,
                        "keywords": draft.keywords,
                        "based_on": draft.based_on.id,
                    }
                )
                based_on_rev = draft.based_on
                rev_form = RevisionForm(instance=instance, initial=rev_initial)
        else:
            which_form = request.POST.get("form", "both")
            doc_form_invalid = False

            if doc:
                _document_lock_clear(doc.id, user.username)

            if user_has_doc_perm and which_form in ["doc", "both"]:
                disclose_description = True
                post_data = request.POST.copy()
                post_data.update({"locale": request.LANGUAGE_CODE})
                doc_form = DocumentForm(post_data, instance=doc)
                doc_form.instance.locale = request.LANGUAGE_CODE
                doc_form.instance.parent = parent_doc
                if which_form == "both":
                    rev_form = RevisionForm(request.POST)

                # If we are submitting the whole form, we need to check that
                # the Revision is valid before saving the Document.
                if doc_form.is_valid() and (which_form == "doc" or rev_form.is_valid()):
                    doc = doc_form.save(parent_doc)

                    # Possibly schedule a rebuild.
                    _maybe_schedule_rebuild(doc_form)

                    if which_form == "doc":
                        url = urlparams(
                            reverse("wiki.edit_document", args=[doc.slug]), opendescription=1
                        )
                        return HttpResponseRedirect(url)

                    doc_slug = doc_form.cleaned_data["slug"]
                else:
                    doc_form_invalid = True
            else:
                doc_slug = doc.slug

            if doc and user_has_rev_perm and which_form in ["rev", "both"]:
                rev_form = RevisionForm(request.POST)
                rev_form.instance.document = doc  # for rev_form.clean()

                if rev_form.is_valid() and not doc_form_invalid:
                    if "no-update" in request.POST:
                        # Keep the old based_on.
                        based_on_id = base_rev.based_on_id
                    else:
                        # Keep what was in the form.
                        based_on_id = None
                    if draft:
                        draft.delete()
                    _save_rev_and_notify(
                        rev_form, request.user, doc, based_on_id, base_rev=base_rev
                    )

                    if "notify-future-changes" in request.POST:
                        EditDocumentEvent.notify(request.user, doc)

                    return HttpResponseRedirect(
                        reverse("wiki.document_revisions", args=[doc_slug])
                    )

    show_revision_warning = _show_revision_warning(doc, base_rev)

    # A list of the revisions that have been approved since the last
    # translation.
    recent_approved_revs = parent_doc.revisions.filter(is_approved=True, id__lte=based_on_rev.id)
    if doc and doc.current_revision and doc.current_revision.based_on_id:
        recent_approved_revs = recent_approved_revs.filter(id__gt=doc.current_revision.based_on_id)

    if doc:
        locked, locked_by = _document_lock(doc.id, user.username)
        # Most updated rev according to based on revision
        more_updated_rev = (
            doc.revisions.filter(based_on__id__gt=based_on_rev.id).order_by("based_on__id").last()
        )
    else:
        locked, locked_by = False, None
        more_updated_rev = None

    return render(
        request,
        "wiki/translate.html",
        {
            "parent": parent_doc,
            "document": doc,
            "document_form": doc_form,
            "revision_form": rev_form,
            "locale": request.LANGUAGE_CODE,
            "based_on": based_on_rev,
            "disclose_description": disclose_description,
            "show_revision_warning": show_revision_warning,
            "recent_approved_revs": recent_approved_revs,
            "locked": locked,
            "locked_by": locked_by,
            "draft_revision": draft,
            "more_updated_rev": more_updated_rev,
        },
    )


@require_POST
@login_required
def watch_document(request, document_slug):
    """Start watching a document for edits."""
    document = get_visible_document_or_404(
        request.user, locale=request.LANGUAGE_CODE, slug=document_slug
    )
    EditDocumentEvent.notify(request.user, document)
    return HttpResponseRedirect(document.get_absolute_url())


@require_POST
@login_required
def unwatch_document(request, document_slug):
    """Stop watching a document for edits."""
    document = get_visible_document_or_404(
        request.user, locale=request.LANGUAGE_CODE, slug=document_slug
    )
    EditDocumentEvent.stop_notifying(request.user, document)
    return HttpResponseRedirect(document.get_absolute_url())


@require_POST
@login_required
def watch_locale(request, product=None):
    """Start watching a locale for revisions ready for review."""
    kwargs = {"locale": request.LANGUAGE_CODE}
    if product is not None:
        kwargs["product"] = product
    ReviewableRevisionInLocaleEvent.notify(request.user, **kwargs)

    return HttpResponse()


@require_POST
@login_required
def unwatch_locale(request, product=None):
    """Stop watching a locale for revisions ready for review."""
    kwargs = {"locale": request.LANGUAGE_CODE}
    if product is not None:
        kwargs["product"] = product
    ReviewableRevisionInLocaleEvent.stop_notifying(request.user, **kwargs)

    return HttpResponse()


@require_POST
@login_required
def watch_approved(request, product=None):
    """Start watching approved revisions in a locale for a given product."""
    if request.LANGUAGE_CODE not in settings.SUMO_LANGUAGES:
        raise Http404

    kwargs = {"locale": request.LANGUAGE_CODE}
    if product is not None:
        kwargs["product"] = product
    ApproveRevisionInLocaleEvent.notify(request.user, **kwargs)

    return HttpResponse()


@require_POST
@login_required
def unwatch_approved(request, product=None):
    """Stop watching approved revisions for a given product."""
    if request.LANGUAGE_CODE not in settings.SUMO_LANGUAGES:
        raise Http404

    kwargs = {"locale": request.LANGUAGE_CODE}
    if product is not None:
        kwargs["product"] = product
    ApproveRevisionInLocaleEvent.stop_notifying(request.user, **kwargs)

    return HttpResponse()


@require_POST
@login_required
def watch_ready(request, product=None):
    """Start watching ready-for-l10n revisions for given product."""
    if request.LANGUAGE_CODE != settings.WIKI_DEFAULT_LANGUAGE:
        raise Http404

    kwargs = {}
    if product is not None:
        kwargs["product"] = product
    ReadyRevisionEvent.notify(request.user, **kwargs)

    return HttpResponse()


@require_POST
@login_required
def unwatch_ready(request, product=None):
    """Stop watching ready-for-l10n revisions for a given product."""
    if request.LANGUAGE_CODE != settings.WIKI_DEFAULT_LANGUAGE:
        raise Http404

    kwargs = {}
    if product is not None:
        kwargs["product"] = product
    ReadyRevisionEvent.stop_notifying(request.user, **kwargs)

    return HttpResponse()


@require_GET
def json_view(request):
    """Return some basic document info in a JSON blob."""
    kwargs = {"locale": request.LANGUAGE_CODE, "current_revision__isnull": False}
    if "title" in request.GET:
        kwargs["title"] = request.GET["title"]
    elif "slug" in request.GET:
        kwargs["slug"] = request.GET["slug"]
    else:
        return HttpResponseBadRequest()

    document = get_object_or_404(Document, **kwargs)
    data = json.dumps(
        {
            "id": document.id,
            "locale": document.locale,
            "slug": document.slug,
            "title": document.title,
            "summary": document.current_revision.summary,
            "url": document.get_absolute_url(),
        }
    )
    return HttpResponse(data, content_type="application/json")


@require_POST
@ratelimit("document-vote", "10/d")
def handle_vote(request, document_slug):
    """Handle both helpful/unhelpful votes and unhelpful surveys."""
    if "revision_id" not in request.POST:
        return HttpResponseBadRequest()

    if "vote_id" in request.POST:
        # Handle survey submission
        vote = get_object_or_404(HelpfulVote, id=smart_int(request.POST["vote_id"]))

        # Only save the survey if there's no already one
        if not vote.metadata.filter(key="survey").exists():
            survey = request.POST.copy()
            survey.pop("vote_id")
            survey.pop("revision_id", None)

            # Save the survey in JSON format, ensuring it doesn't exceed 600 chars
            vote.add_metadata("survey", truncated_json_dumps(survey, 600, "comment"))
        survey_response = render_to_string(
            "wiki/includes/survey_form.html",
            {"response_message": _("Thanks for making us better!")},
            request,
        )
        return HttpResponse(survey_response)

    # Handle helpful/unhelpful voting
    revision = get_object_or_404(Revision, id=smart_int(request.POST["revision_id"]))

    if not revision.is_approved:
        raise PermissionDenied

    if revision.document.category == TEMPLATES_CATEGORY:
        return HttpResponseBadRequest()

    survey_context = {}

    if not revision.has_voted(request):
        ua = request.META.get("HTTP_USER_AGENT", "")[:1000]  # Limit to 1000 characters
        vote = HelpfulVote.objects.create(revision=revision, user_agent=ua)
        survey_context = {
            "vote_id": vote.id,
            "action_url": reverse("wiki.document_vote", args=[document_slug]),
            "revision_id": revision.id,
            "response_message": "",
        }

        if "helpful" in request.POST:
            vote.helpful = True
            survey_context.update(
                {
                    "survey_type": "helpful",
                    "survey_heading": _('You voted "Yes 👍" Please tell us more'),
                    "survey_options": [
                        {"value": "article-accurate", "text": _("Article is accurate")},
                        {
                            "value": "article-easy-to-understand",
                            "text": _("Article is easy to understand"),
                        },
                        {"value": "article-helpful-visuals", "text": _("The visuals are helpful")},
                        {
                            "value": "article-informative",
                            "text": _("Article provided the information I needed"),
                        },
                        {"value": "other", "text": _("Other")},
                    ],
                }
            )
        else:
            survey_context.update(
                {
                    "survey_type": "unhelpful",
                    "survey_heading": _('You voted "No 👎" Please tell us more'),
                    "survey_options": [
                        {"value": "article-inaccurate", "text": _("Article is inaccurate")},
                        {"value": "article-confusing", "text": _("Article is confusing")},
                        {
                            "value": "article-not-helpful-visuals",
                            "text": _("Missing, unclear, or unhelpful visuals"),
                        },
                        {
                            "value": "article-not-informative",
                            "text": _("Article didn't provide the information I needed"),
                        },
                        {"value": "other", "text": _("Other")},
                    ],
                }
            )

        # If the user is over the limit,pretend everything is fine without saving
        if not request.limited:
            if request.user.is_authenticated:
                vote.creator = request.user
            else:
                vote.anonymous_id = request.anonymous.anonymous_id

            vote.save()

            # Save metadata: referrer and search query (if available)
            for name in ["referrer", "query", "source"]:
                val = request.POST.get(name)
                if val:
                    vote.add_metadata(name, val)

    if request.headers.get("HX-Request") and survey_context:
        survey_html = render_to_string("wiki/includes/survey_form.html", survey_context, request)
        return HttpResponse(survey_html)
    return HttpResponseRedirect(revision.document.get_absolute_url())


@require_GET
def get_helpful_votes_async(request, document_slug):
    document = get_visible_document_or_404(
        request.user, locale=request.LANGUAGE_CODE, slug=document_slug
    )

    datums = []
    flag_data = []
    rev_data = []
    revisions = set()
    created_list = []
    timestamps_with_data = set()

    results = (
        HelpfulVote.objects.filter(revision__document=document)
        .values(date_created=TruncDate("created"))
        .annotate(
            revisions=ArrayAgg("revision_id"),
            count_helpful=Count("helpful", filter=Q(helpful=True)),
            count_unhelpful=Count("helpful", filter=Q(helpful=False)),
        )
        .order_by("date_created")
    )

    for res in results:
        revisions.update(res["revisions"])
        created_list.append(res["date_created"])
        timestamp = (time.mktime(res["date_created"].timetuple()) // 86400) * 86400

        datums.append(
            {
                "yes": res["count_helpful"],
                "no": res["count_unhelpful"],
                "date": timestamp,
            }
        )
        timestamps_with_data.add(timestamp)

    if not created_list:
        send = {"datums": [], "annotations": []}
        return HttpResponse(json.dumps(send), content_type="application/json")

    # The "created_list" is a list of date objects, while "min_created" and
    # "max_created" are datetime objects that span the period from the beginning
    # of the first day to the end of the last day that the document was voted on.
    min_created = datetime.combine(min(created_list), datetime_time.min)
    max_created = datetime.combine(max(created_list), datetime_time.max)

    # Zero fill the data.
    end = time.mktime(datetime.now().timetuple())
    while timestamp <= end:
        if timestamp not in timestamps_with_data:
            datums.append(
                {
                    "yes": 0,
                    "no": 0,
                    "date": timestamp,
                }
            )
            timestamps_with_data.add(timestamp)
        timestamp += 24 * 60 * 60

    for flag in ImportantDate.objects.filter(date__gte=min_created, date__lte=max_created):
        flag_data.append({"x": int(time.mktime(flag.date.timetuple())), "text": _(flag.text)})

    for rev in Revision.objects.filter(
        pk__in=revisions, created__range=(min_created, max_created)
    ):
        rdate = rev.reviewed or rev.created
        rev_data.append(
            {"x": int(time.mktime(rdate.timetuple())), "text": str(_("Revision %s")) % rev.created}
        )

    # Rickshaw wants data like
    # [{'name': 'series1', 'data': [{'x': 1362774285, 'y': 100}, ...]},]
    send = {"datums": datums, "annotations": []}

    if flag_data:
        send["annotations"].append(
            {
                "name": _("Firefox Releases"),
                "slug": "releases",
                "data": flag_data,
            }
        )
    if rev_data:
        send["annotations"].append(
            {
                "name": _("Article Revisions"),
                "slug": "revisions",
                "data": rev_data,
            }
        )

    return HttpResponse(json.dumps(send), content_type="application/json")


@login_required
def delete_revision(request, document_slug, revision_id):
    """Delete a revision."""
    revision = get_visible_revision_or_404(
        request.user,
        pk=revision_id,
        document__slug=document_slug,
        document__locale=request.LANGUAGE_CODE,
    )
    document = revision.document

    if not document.allows(request.user, "delete_revision"):
        raise PermissionDenied

    only_revision = document.revisions.count() == 1
    helpful_votes = HelpfulVote.objects.filter(revision=revision.id)
    has_votes = helpful_votes.exists()

    if request.method == "GET":
        # Render the confirmation page
        return render(
            request,
            "wiki/confirm_revision_delete.html",
            {
                "revision": revision,
                "document": document,
                "only_revision": only_revision,
                "has_votes": has_votes,
            },
        )

    # Don't delete the only revision of a document
    if only_revision:
        return HttpResponseBadRequest()

    log.warning("User %s is deleting revision with id=%s" % (request.user, revision.id))
    revision.delete()
    return HttpResponseRedirect(reverse("wiki.document_revisions", args=[document.slug]))


@login_required
@require_POST
def mark_ready_for_l10n_revision(request, document_slug, revision_id):
    """Mark a revision as ready for l10n."""
    revision = get_visible_revision_or_404(
        request.user,
        pk=revision_id,
        document__slug=document_slug,
        document__locale=settings.WIKI_DEFAULT_LANGUAGE,
    )

    if not revision.document.allows(request.user, "mark_ready_for_l10n"):
        raise PermissionDenied

    if revision.can_be_readied_for_localization():
        # We don't use update(), because that wouldn't update
        # Document.latest_localizable_revision.
        revision.is_ready_for_localization = True
        revision.readied_for_localization = datetime.now()
        revision.readied_for_localization_by = request.user
        revision.save()

        ReadyRevisionEvent(revision).fire(exclude=[request.user])

        return HttpResponse(json.dumps({"message": revision_id}))

    return HttpResponseBadRequest()


@login_required
def delete_document(request, document_slug):
    """Delete a document."""
    document = get_visible_document_or_404(
        request.user, locale=request.LANGUAGE_CODE, slug=document_slug
    )

    # Check permission
    if not document.allows(request.user, "delete"):
        raise PermissionDenied

    if request.method == "GET":
        # Render the confirmation page
        return render(request, "wiki/confirm_document_delete.html", {"document": document})

    # Handle confirm delete form POST
    log.warning(
        "User %s is deleting document: %s (id=%s)" % (request.user, document.title, document.id)
    )
    document.delete()

    return render(
        request,
        "wiki/confirm_document_delete.html",
        {"document": document, "delete_confirmed": True},
    )


@login_required
@require_POST
def add_contributor(request, document_slug):
    """Add a contributor to a document."""
    document = get_visible_document_or_404(
        request.user, locale=request.LANGUAGE_CODE, slug=document_slug
    )

    if not document.allows(request.user, "edit"):
        raise PermissionDenied

    form = AddContributorForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data["users"]:
            document.contributors.add(user)
        msg = _("{users} added to the contributors successfully!").format(
            users=request.POST.get("users")
        )
        messages.add_message(request, messages.SUCCESS, msg)

        return HttpResponseRedirect(reverse("wiki.document_revisions", args=[document_slug]))

    msg = _("There were errors adding new contributors, see below.")
    messages.add_message(request, messages.ERROR, msg)
    return document_revisions(request, document_slug, contributor_form=form)


@login_required
@require_http_methods(["GET", "POST"])
def remove_contributor(request, document_slug, user_id):
    """Remove a contributor from a document."""
    document = get_visible_document_or_404(
        request.user, locale=request.LANGUAGE_CODE, slug=document_slug
    )

    if not document.allows(request.user, "edit"):
        raise PermissionDenied

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        document.contributors.remove(user)
        msg = _("{user} removed from the contributors successfully!").format(user=user.username)
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(reverse("wiki.document_revisions", args=[document_slug]))

    return render(
        request,
        "wiki/confirm_remove_contributor.html",
        {"document": document, "contributor": user},
    )


def show_translations(request, document_slug):
    document = get_visible_document_or_404(
        request.user, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug
    )

    translated_locales = []
    untranslated_locales = []

    # Makes Sure "English (en-US)" is always on top
    translated_locales.append((document.locale, LOCALES[document.locale].native))
    # Gets all the translated locale codes
    translated_locales_code = document.translations.all().values_list("locale", flat=True)

    for locale in settings.LANGUAGE_CHOICES:
        if locale[0] in translated_locales_code:
            translated_locales.append(locale)
        else:
            untranslated_locales.append(locale)

    return render(
        request,
        "wiki/show_translations.html",
        {
            "document": document,
            "translated_locales": translated_locales,
            "untranslated_locales": untranslated_locales,
        },
    )


def _document_form_initial(document):
    """Return a dict with the document data pertinent for the form."""
    return {
        "title": document.title,
        "slug": document.slug,
        "category": document.category,
        "is_localizable": document.is_localizable,
        "is_archived": document.is_archived,
        "topics": Topic.active.filter(document=document).values_list("id", flat=True),
        "products": list(Product.active.filter(document=document).values_list("id", flat=True)),
        "related_documents": Document.objects.filter(related_documents=document).values_list(
            "id", flat=True
        ),
        "allow_discussion": document.allow_discussion,
        "needs_change": document.needs_change,
        "needs_change_comment": document.needs_change_comment,
        "restrict_to_groups": document.restrict_to_groups.all(),
    }


def _save_rev_and_notify(rev_form, creator, document, based_on_id=None, base_rev=None):
    """Save the given RevisionForm and send notifications."""
    new_rev = rev_form.save(creator, document, based_on_id, base_rev)

    # Enqueue notifications
    ReviewableRevisionInLocaleEvent(new_rev).fire(exclude=[new_rev.creator])
    EditDocumentEvent(new_rev).fire(exclude=[new_rev.creator])


def _maybe_schedule_rebuild(form):
    """Try to schedule a KB rebuild if a title or slug has changed."""
    if "title" in form.changed_data or "slug" in form.changed_data:
        schedule_rebuild_kb()


def _get_next_url_fallback_localization(request):
    return get_next_url(request) or reverse("dashboards.localization")


def _show_revision_warning(document, revision):
    if revision:
        return document.revisions.filter(id__gt=revision.id, reviewed=None).exists()
    return False


def recent_revisions(request):
    request.GET = request.GET.copy()
    fragment = request.GET.pop("fragment", None)
    form = RevisionFilterForm(request.GET)

    # Validate the form to populate cleaned_data, even with invalid usernames.
    form.is_valid()

    filters = {}
    if hasattr(form, "cleaned_data"):
        if form.cleaned_data.get("locale"):
            filters.update(document__locale=form.cleaned_data["locale"])

        # Only apply user filter if there are valid users
        if form.cleaned_data.get("users"):
            filters.update(creator__in=form.cleaned_data["users"])

        start = form.cleaned_data.get("start")
        end = form.cleaned_data.get("end")
        if start or end:
            filters.update(created__range=(start or datetime.min, end or Now()))

    revs = Revision.objects.visible(request.user, **filters).order_by("-created")

    revs = paginate(request, revs)

    c = {
        "revisions": revs,
        "form": form,
        "locale": request.GET.get("locale", request.LANGUAGE_CODE),
    }
    if fragment:
        template = "wiki/includes/recent_revisions_fragment.html"
    else:
        template = "wiki/recent_revisions.html"

    return render(request, template, c)


@require_GET
def what_links_here(request, document_slug):
    """List all documents that link to a document."""
    locale = request.GET.get("locale", request.LANGUAGE_CODE)

    doc = get_visible_document_or_404(
        request.user,
        locale=locale,
        slug=document_slug,
        look_for_translation_via_parent=True,
    )

    if doc.slug != document_slug:
        # We've found the translation at a different slug.
        url = reverse("wiki.what_links_here", args=[doc.slug], locale=locale)
        return HttpResponseRedirect(url)

    links = {}
    links_to = (
        doc.links_to()
        .filter(Exists(Document.objects.visible(request.user, id=OuterRef("linked_from"))))
        .select_related("linked_from")
    )
    for link_to in links_to:
        if doc.locale == link_to.linked_from.locale:
            if link_to.kind not in links:
                links[link_to.kind] = []
            links[link_to.kind].append(link_to.linked_from)

    ctx = {"document": doc, "relations": links}

    return render(request, "wiki/what_links_here.html", ctx)


def get_fallback_locale(doc, request):
    """
    Attempt to find an acceptable fallback locale. Returns a tuple comprised of
    the locale (None if no acceptable locale is found) and a boolean indicating
    whether or not the incoming Accept-Language header could have been used to
    determine the fallback locale.
    """

    # Get locales that the current article is translated into.
    translated_locales = set(
        doc.translations.values_list("locale", flat=True).exclude(current_revision=None)
    )

    # Build a list of the request locale and all the ACCEPT_LANGUAGE locales.
    all_acceptable_locales = [request.LANGUAGE_CODE.lower()]
    # Django's "parse_accept_lang_header()" always returns lowercase locales.
    accept_header = request.META.get("HTTP_ACCEPT_LANGUAGE") or ""
    all_acceptable_locales.extend(loc for loc, _ in parse_accept_lang_header(accept_header))

    # For each locale specified in the user's ACCEPT_LANGUAGE header
    # check for, in order:
    #   * no fallback for "en-US" in accept language header
    #   * translations in that locale
    #   * global overrides for the locale in settings.NON_SUPPORTED_LOCALES
    #   * wiki fallbacks for that locale

    # In the loop below, return true for the second part of the result tuple
    # only if we're past the first iteration, since only then have we used
    # a locale from the incoming Accept-Language header. The first iteration
    # of the loop only uses the locale provided in the incoming URL.

    for i, locale in enumerate(all_acceptable_locales):
        if locale == settings.WIKI_DEFAULT_LANGUAGE.lower():
            return (None, i > 0)

        elif (normalized_locale := normalize_language(locale)) in translated_locales:
            # This path handles the settings.NON_SUPPORTED_LOCALES cases as well.
            return (normalized_locale, i > 0)

        for fallback in FALLBACK_LOCALES.get(locale, []):
            if fallback in translated_locales:
                return (fallback, i > 0)

    # If all else fails, return None as the fallback locale, and return "True" for
    # the second part of the result tuple, because if we've reached this point, the
    # incoming Accept-Language header could have influenced the result.
    return (None, True)


def pocket_article(request, article_id=None, document_slug=None, extra_path=None):
    """Pocket articles migrated to SUMO are redirected to the new URL"""
    # If we migrated the document, we should be able to find it
    if Document.objects.visible(request.user, slug=document_slug).exists():
        return HttpResponseRedirect(reverse("wiki.document", args=[document_slug]))
    # If document doesn't exist, fail back to Pocket product page with message
    messages.warning(
        request,
        _("Sorry, that article wasn't found."),
    )
    return redirect(product_landing, slug="pocket", permanent=True)
