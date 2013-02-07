from datetime import datetime
import json
import logging
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.http import (HttpResponse, HttpResponseRedirect,
                         Http404, HttpResponseBadRequest)
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (require_GET, require_POST,
                                          require_http_methods)

import jingo
import waffle
from mobility.decorators import mobile_template
from statsd import statsd
from tower import ugettext_lazy as _lazy
from tower import ugettext as _

from access.decorators import permission_required, login_required
from products.models import Product
from sumo.helpers import urlparams
from sumo.redis_utils import redis_client, RedisError
from sumo.urlresolvers import reverse
from sumo.utils import paginate, smart_int, get_next_url, truncated_json_dumps
from topics.models import Topic
from wiki import DOCUMENTS_PER_PAGE
from wiki.events import (EditDocumentEvent, ReviewableRevisionInLocaleEvent,
                         ApproveRevisionInLocaleEvent, ApprovedOrReadyUnion,
                         ReadyRevisionEvent)
from wiki.forms import (AddContributorForm, DocumentForm, RevisionForm,
                        ReviewForm)
from wiki.models import Document, Revision, HelpfulVote, ImportantDate
from wiki.config import CATEGORIES, TEMPLATES_CATEGORY
from wiki.parser import wiki_to_html
from wiki.showfor import showfor_data
from wiki.tasks import (send_reviewed_notification, schedule_rebuild_kb,
                        send_contributor_notification)


log = logging.getLogger('k.wiki')


@require_GET
def landing(request, template='wiki/landing.html'):
    """The KB landing page.

    Lists topics and products.
    """
    return jingo.render(request, template, {
        'products': Product.objects.filter(visible=True),
        'topics': Topic.objects.filter(visible=True)})


@require_GET
@mobile_template('wiki/{mobile/}document.html')
def document(request, document_slug, template=None):
    """View a wiki document."""
    fallback_reason = None
    # If a slug isn't available in the requested locale, fall back to en-US:
    try:
        doc = Document.objects.get(locale=request.LANGUAGE_CODE, slug=document_slug)
        if (not doc.current_revision and doc.parent and
            doc.parent.current_revision):
            # This is a translation but its current_revision is None
            # and OK to fall back to parent (parent is approved).
            fallback_reason = 'translation_not_approved'
        elif not doc.current_revision:
            # No current_revision, no parent with current revision, so
            # nothing to show.
            fallback_reason = 'no_content'
    except Document.DoesNotExist:
        # Look in default language:
        doc = get_object_or_404(Document,
                                locale=settings.WIKI_DEFAULT_LANGUAGE,
                                slug=document_slug)
        # If there's a translation to the requested locale, take it:
        translation = doc.translated_to(request.LANGUAGE_CODE)
        if translation:
            url = translation.get_absolute_url()
            url = urlparams(url, query_dict=request.GET)
            return HttpResponseRedirect(url)
        elif doc.current_revision:
            # There is no translation
            # and OK to fall back to parent (parent is approved).
            fallback_reason = 'no_translation'

    # Obey explicit redirect pages:
    # Don't redirect on redirect=no (like Wikipedia), so we can link from a
    # redirected-to-page back to a "Redirected from..." link, so you can edit
    # the redirect.
    redirect_url = (None if request.GET.get('redirect') == 'no'
                    else doc.redirect_url(request.LANGUAGE_CODE))
    if redirect_url:
        url = urlparams(redirect_url, query_dict=request.GET,
                        redirectslug=doc.slug, redirectlocale=doc.locale)
        return HttpResponseRedirect(url)

    # Get "redirected from" doc if we were redirected:
    redirect_slug = request.GET.get('redirectslug')
    redirect_locale = request.GET.get('redirectlocale')
    redirected_from = None
    if redirect_slug and redirect_locale:
        try:
            redirected_from = Document.objects.get(locale=redirect_locale,
                                                   slug=redirect_slug)
        except Document.DoesNotExist:
            pass

    related = doc.related_documents[:3]

    contributors = doc.contributors.all()

    products = doc.get_products()
    if len(products) < 1:
        product = Product.objects.filter(visible=True)[0]
    else:
        product = products[0]

    topics = Topic.objects.filter(visible=True)

    hide_voting = False
    if (doc.category == TEMPLATES_CATEGORY or
        waffle.switch_is_active('hide-voting')):
        hide_voting = True
    data = {'document': doc, 'redirected_from': redirected_from,
            'related': related, 'contributors': contributors,
            'fallback_reason': fallback_reason,
            'is_aoa_referral': request.GET.get('ref') == 'aoa',
            'topics': topics, 'product': product, 'products': products,
            'hide_voting': hide_voting}
    data.update(showfor_data(products))
    return jingo.render(request, template, data)


def revision(request, document_slug, revision_id):
    """View a wiki document revision."""
    rev = get_object_or_404(Revision, pk=revision_id,
                            document__slug=document_slug)
    data = {'document': rev.document, 'revision': rev}
    data.update(showfor_data())
    return jingo.render(request, 'wiki/revision.html', data)


@require_GET
def list_documents(request, category=None, topic=None):
    """List wiki documents."""
    docs = Document.objects.filter(locale=request.LANGUAGE_CODE).order_by('title')
    if category:
        docs = docs.filter(category=category)
        try:
            category_id = int(category)
        except ValueError:
            raise Http404
        try:
            category = unicode(dict(CATEGORIES)[category_id])
        except KeyError:
            raise Http404

    if topic:
        topic = get_object_or_404(Topic, slug=topic)
        default_lang = settings.WIKI_DEFAULT_LANGUAGE
        if request.LANGUAGE_CODE == default_lang:
            docs = docs.filter(topics=topic)
        else:
            parent_ids = Document.objects.filter(
                locale=default_lang, topics=topic).values_list('id', flat=True)
            docs = docs.filter(parent__in=parent_ids)

    docs = paginate(request, docs, per_page=DOCUMENTS_PER_PAGE)
    return jingo.render(request, 'wiki/list_documents.html',
                        {'documents': docs,
                         'category': category,
                         'topic': topic.title if topic else None})


@login_required
def new_document(request):
    """Create a new wiki document."""
    if request.method == 'GET':
        doc_form = DocumentForm(initial_title=request.GET.get('title'))
        rev_form = RevisionForm()
        return jingo.render(request, 'wiki/new_document.html',
                            {'document_form': doc_form,
                             'revision_form': rev_form})

    post_data = request.POST.copy()
    post_data.update({'locale': request.LANGUAGE_CODE})
    doc_form = DocumentForm(post_data)
    rev_form = RevisionForm(post_data)

    if doc_form.is_valid() and rev_form.is_valid():
        doc = doc_form.save(None)
        _save_rev_and_notify(rev_form, request.user, doc)
        return HttpResponseRedirect(reverse('wiki.document_revisions',
                                    args=[doc.slug]))

    return jingo.render(request, 'wiki/new_document.html',
                        {'document_form': doc_form,
                         'revision_form': rev_form})


_document_lock_key = 'sumo::wiki::document::{id}::lock'


def _document_lock_check(document_id):
    """Check for a lock on a document.

    Returns the username of the user that has the page locked, or ``None`` if
    no user has a lock.
    """
    try:
        redis = redis_client(name='default')
        key = _document_lock_key.format(id=document_id)
        return redis.get(key)
    except RedisError as e:
        statsd.incr('redis.errror')
        log.error('Redis error: %s' % e)
        return None


def _document_lock_steal(document_id, user_name, expire_time=60 * 15):
    """Lock a document for a user.

    Note that this does not check if the page is already locked, and simply
    sets the lock on the page.
    """
    try:
        redis = redis_client(name='default')
        key = _document_lock_key.format(id=document_id)
        it_worked = redis.set(key, user_name)
        redis.expire(key, expire_time)
        return it_worked
    except RedisError as e:
        statsd.incr('redis.errror')
        log.error('Redis error: %s' % e)
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
        redis = redis_client(name='default')
        key = _document_lock_key.format(id=document_id)
        locked_by = redis.get(key)
        if locked_by == user_name:
            return redis.delete(key)
        else:
            return False
    except RedisError as e:
        statsd.incr('redis.errror')
        log.error('Redis error: %s' % e)
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
            # If the user doesn't exist, they shouldn't be able to enforce a lock.
            locked = False
            locked_by = None
    else:
        locked_by = username
        locked = False
        _document_lock_steal(doc_id, username)

    return locked, locked_by


@login_required
def steal_lock(request, document_slug, revision_id=None):
    doc = get_object_or_404(
        Document, locale=request.LANGUAGE_CODE, slug=document_slug)
    user = request.user

    ok = _document_lock_steal(doc.id, user.username)
    return HttpResponse("", status=200 if ok else 400)


@require_http_methods(['GET', 'POST'])
@login_required  # TODO: Stop repeating this knowledge here and in
                 # Document.allows_editing_by.
def edit_document(request, document_slug, revision_id=None):
    """Create a new revision of a wiki document, or edit document metadata."""
    doc = get_object_or_404(
        Document, locale=request.LANGUAGE_CODE, slug=document_slug)
    user = request.user

    # If this document has a parent, then the edit is handled by the
    # translate view. Pass it on.
    if doc.parent:
        return translate(request, doc.parent.slug, revision_id)
    if revision_id:
        rev = get_object_or_404(Revision, pk=revision_id, document=doc)
    else:
        rev = doc.current_revision or doc.revisions.order_by('-created',
                                                             '-id')[0]

    disclose_description = bool(request.GET.get('opendescription'))
    doc_form = rev_form = None
    if doc.allows_revision_by(user):
        rev_form = RevisionForm(
            instance=rev,
            initial={'based_on': rev.id, 'comment': ''})
    if doc.allows_editing_by(user):
        doc_form = DocumentForm(
            initial=_document_form_initial(doc),
            can_archive=user.has_perm('wiki.archive_document'))

    if request.method == 'GET':
        if not (rev_form or doc_form):
            # You can't do anything on this page, so get lost.
            raise PermissionDenied

    else:  # POST
        # Comparing against localized names for the Save button bothers me, so
        # I embedded a hidden input:
        which_form = request.POST.get('form')

        _document_lock_clear(doc.id, user.username)

        if which_form == 'doc':
            if doc.allows_editing_by(user):
                post_data = request.POST.copy()
                post_data.update({'locale': request.LANGUAGE_CODE})
                doc_form = DocumentForm(
                    post_data,
                    instance=doc,
                    can_archive=user.has_perm('wiki.archive_document'))
                if doc_form.is_valid():
                    # Get the possibly new slug for the imminent redirection:
                    doc = doc_form.save(None)

                    # Do we need to rebuild the KB?
                    _maybe_schedule_rebuild(doc_form)

                    return HttpResponseRedirect(
                        urlparams(reverse('wiki.edit_document',
                                          args=[doc.slug]),
                                  opendescription=1))
                disclose_description = True
            else:
                raise PermissionDenied
        elif which_form == 'rev':
            if doc.allows_revision_by(user):
                rev_form = RevisionForm(request.POST)
                rev_form.instance.document = doc  # for rev_form.clean()
                if rev_form.is_valid():
                    _save_rev_and_notify(rev_form, user, doc)
                    if 'notify-future-changes' in request.POST:
                        EditDocumentEvent.notify(request.user, doc)

                    return HttpResponseRedirect(
                        reverse('wiki.document_revisions',
                                args=[document_slug]))
            else:
                raise PermissionDenied

    show_revision_warning = _show_revision_warning(doc, rev)

    locked, locked_by = _document_lock(doc.id, user.username)

    return jingo.render(request, 'wiki/edit.html',
                        {'revision_form': rev_form,
                         'document_form': doc_form,
                         'disclose_description': disclose_description,
                         'document': doc,
                         'show_revision_warning': show_revision_warning,
                         'locked': locked,
                         'locked_by': locked_by})


@login_required
@require_POST
def preview_revision(request):
    """Create an HTML fragment preview of the posted wiki syntax."""
    wiki_content = request.POST.get('content', '')
    statsd.incr('wiki.preview')
    # TODO: Get doc ID from JSON.
    data = {'content': wiki_to_html(wiki_content, request.LANGUAGE_CODE)}
    data.update(showfor_data())
    return jingo.render(request, 'wiki/preview.html', data)


@require_GET
def document_revisions(request, document_slug, contributor_form=None):
    """List all the revisions of a given document."""
    locale = request.GET.get('locale', request.LANGUAGE_CODE)
    doc = get_object_or_404(
        Document, locale=locale, slug=document_slug)
    revs = Revision.objects.filter(document=doc).order_by('-created', '-id')

    if request.is_ajax():
        template = 'wiki/includes/revision_list.html'
    else:
        template = 'wiki/history.html'

    form = contributor_form or AddContributorForm()
    return jingo.render(request, template,
                        {'revisions': revs, 'document': doc,
                         'contributor_form': form})


@login_required
@permission_required('wiki.review_revision')
def review_revision(request, document_slug, revision_id):
    """Review a revision of a wiki document."""
    rev = get_object_or_404(Revision, pk=revision_id,
                            document__slug=document_slug)
    doc = rev.document
    form = ReviewForm(
        initial={'needs_change': doc.needs_change,
                 'needs_change_comment': doc.needs_change_comment})

    # Don't ask significance if this doc is a translation or if it has no
    # former approved versions:
    should_ask_significance = not doc.parent and doc.current_revision

    based_on_revs = doc.revisions.all()
    last_approved_date = getattr(doc.current_revision, 'created',
                                   datetime.fromordinal(1))
    based_on_revs = based_on_revs.filter(created__gt=last_approved_date)
    revision_contributors = list(set(
        based_on_revs.values_list('creator__username', flat=True)))

    # Don't include the reviewer in the recent contributors list.
    if request.user.username in revision_contributors:
        revision_contributors.remove(request.user.username)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid() and not rev.reviewed:
            # Don't allow revisions to be reviewed twice
            rev.is_approved = 'approve' in request.POST
            rev.reviewer = request.user
            rev.reviewed = datetime.now()
            if should_ask_significance and form.cleaned_data['significance']:
                rev.significance = form.cleaned_data['significance']

            # If document is localizable and revision was approved and
            # user has permission, set the is_ready_for_localization value.
            if (doc.is_localizable and rev.is_approved and
                request.user.has_perm('wiki.mark_ready_for_l10n')):
                rev.is_ready_for_localization = form.cleaned_data[
                    'is_ready_for_localization']

            rev.save()

            # Update the needs change bit (if approved, default language and
            # user has permission).
            if (doc.locale == settings.WIKI_DEFAULT_LANGUAGE and
                doc.allows_editing_by(request.user) and rev.is_approved):
                doc.needs_change = form.cleaned_data['needs_change']
                doc.needs_change_comment = \
                    form.cleaned_data['needs_change_comment']
                doc.save()

            # Send notifications of approvedness and readiness:
            if rev.is_ready_for_localization or rev.is_approved:
                events = [ApproveRevisionInLocaleEvent(rev)]
                if rev.is_ready_for_localization:
                    events.append(ReadyRevisionEvent(rev))
                ApprovedOrReadyUnion(*events).fire(exclude=[rev.creator,
                                                            request.user])

            # Send an email (not really a "notification" in the sense that
            # there's a Watch table entry) to revision creator.
            msg = form.cleaned_data['comment']
            send_reviewed_notification.delay(rev, doc, msg)
            send_contributor_notification(based_on_revs, rev, doc, msg)

            # Schedule KB rebuild?
            statsd.incr('wiki.review')
            schedule_rebuild_kb()

            return HttpResponseRedirect(reverse('wiki.document_revisions',
                                                args=[document_slug]))

    if doc.parent:  # A translation
        # For diffing the based_on revision against, to help the user see if he
        # translated all the recent changes:
        parent_revision = (rev.based_on or
                           doc.parent.localizable_or_latest_revision())
        template = 'wiki/review_translation.html'
    else:
        parent_revision = None
        template = 'wiki/review_revision.html'

    data = {'revision': rev, 'document': doc, 'form': form,
            'parent_revision': parent_revision,
            'revision_contributors': list(revision_contributors),
            'should_ask_significance': should_ask_significance}
    data.update(showfor_data())
    return jingo.render(request, template, data)


@require_GET
def compare_revisions(request, document_slug):
    """Compare two wiki document revisions.

    The ids are passed as query string parameters (to and from).

    """
    locale = request.GET.get('locale', request.LANGUAGE_CODE)
    doc = get_object_or_404(
        Document, locale=locale, slug=document_slug)
    if 'from' not in request.GET or 'to' not in request.GET:
        raise Http404

    from_id = smart_int(request.GET.get('from'))
    to_id = smart_int(request.GET.get('to'))
    revision_from = get_object_or_404(Revision, document=doc, id=from_id)
    revision_to = get_object_or_404(Revision, document=doc, id=to_id)

    if request.is_ajax():
        template = 'wiki/includes/revision_diff.html'
    else:
        template = 'wiki/compare_revisions.html'

    return jingo.render(request, template,
                        {'document': doc, 'revision_from': revision_from,
                         'revision_to': revision_to})


@login_required
def select_locale(request, document_slug):
    """Select a locale to translate the document to."""
    doc = get_object_or_404(
        Document, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug)
    return jingo.render(request, 'wiki/select_locale.html', {'document': doc})


@require_http_methods(['GET', 'POST'])
@login_required
def translate(request, document_slug, revision_id=None):
    """Create a new translation of a wiki document.

    * document_slug is for the default locale
    * translation is to the request.LANGUAGE_CODE

    """
    # TODO: Refactor this view into two views? (new, edit)
    # That might help reduce the headache-inducing branchiness.
    parent_doc = get_object_or_404(
        Document, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug)
    user = request.user

    if settings.WIKI_DEFAULT_LANGUAGE == request.LANGUAGE_CODE:
        # Don't translate to the default language.
        return HttpResponseRedirect(reverse(
            'wiki.edit_document', locale=settings.WIKI_DEFAULT_LANGUAGE,
            args=[parent_doc.slug]))

    if not parent_doc.is_localizable:
        message = _lazy(u'You cannot translate this document.')
        return jingo.render(request, 'handlers/400.html',
                            {'message': message}, status=400)

    based_on_rev = parent_doc.localizable_or_latest_revision(
        include_rejected=True)

    disclose_description = bool(request.GET.get('opendescription'))

    try:
        doc = parent_doc.translations.get(locale=request.LANGUAGE_CODE)
    except Document.DoesNotExist:
        doc = None
        disclose_description = True

    user_has_doc_perm = ((not doc) or (doc and doc.allows_editing_by(user)))
    user_has_rev_perm = ((not doc) or (doc and doc.allows_revision_by(user)))
    if not user_has_doc_perm and not user_has_rev_perm:
        # User has no perms, bye.
        raise PermissionDenied

    doc_form = rev_form = None
    base_rev = None

    if user_has_doc_perm:
        doc_initial = _document_form_initial(doc) if doc else None
        doc_form = DocumentForm(initial=doc_initial)
    if user_has_rev_perm:
        initial = {'based_on': based_on_rev.id, 'comment': ''}
        if revision_id:
            base_rev = Revision.objects.get(pk=revision_id)
            initial.update(content=base_rev.content,
                           summary=base_rev.summary,
                           keywords=base_rev.keywords)
        elif not doc:
            initial.update(content=based_on_rev.content,
                           summary=based_on_rev.summary,
                           keywords=based_on_rev.keywords)

        # Get a revision of the translation to plonk into the page as a
        # starting point. Since translations are never "ready for
        # localization", this will first try to find an approved revision, then
        # an unrejected one, then give up.
        instance = doc and doc.localizable_or_latest_revision()

        rev_form = RevisionForm(instance=instance, initial=initial)
        base_rev = base_rev or instance

    if request.method == 'POST':
        which_form = request.POST.get('form', 'both')
        doc_form_invalid = False

        if doc is not None:
            _document_lock_clear(doc.id, user.username)

        if user_has_doc_perm and which_form in ['doc', 'both']:
            disclose_description = True
            post_data = request.POST.copy()
            post_data.update({'locale': request.LANGUAGE_CODE})
            doc_form = DocumentForm(post_data, instance=doc)
            doc_form.instance.locale = request.LANGUAGE_CODE
            doc_form.instance.parent = parent_doc
            if which_form == 'both':
                rev_form = RevisionForm(request.POST)

            # If we are submitting the whole form, we need to check that
            # the Revision is valid before saving the Document.
            if doc_form.is_valid() and (which_form == 'doc' or
                                        rev_form.is_valid()):
                doc = doc_form.save(parent_doc)

                # Possibly schedule a rebuild.
                _maybe_schedule_rebuild(doc_form)

                if which_form == 'doc':
                    url = urlparams(reverse('wiki.edit_document',
                                            args=[doc.slug]),
                                    opendescription=1)
                    return HttpResponseRedirect(url)

                doc_slug = doc_form.cleaned_data['slug']
            else:
                doc_form_invalid = True
        else:
            doc_slug = doc.slug

        if doc and user_has_rev_perm and which_form in ['rev', 'both']:
            rev_form = RevisionForm(request.POST)
            rev_form.instance.document = doc  # for rev_form.clean()

            if rev_form.is_valid() and not doc_form_invalid:
                if 'no-update' in request.POST:
                    # Keep the old based_on.
                    based_on_id = base_rev.based_on_id
                else:
                    # Keep what was in the form.
                    based_on_id = None

                _save_rev_and_notify(rev_form, request.user, doc, based_on_id)

                if 'notify-future-changes' in request.POST:
                    EditDocumentEvent.notify(request.user, doc)

                url = reverse('wiki.document_revisions',
                              args=[doc_slug])

                return HttpResponseRedirect(url)

    show_revision_warning = _show_revision_warning(doc, base_rev)

    # A list of the revisions that have been approved since the last
    # translation.
    recent_approved_revs = parent_doc.revisions.filter(
        is_approved=True, id__lte=based_on_rev.id)
    if doc and doc.current_revision and doc.current_revision.based_on_id:
        recent_approved_revs = recent_approved_revs.filter(
            id__gt=doc.current_revision.based_on_id)

    if doc:
        locked, locked_by = _document_lock(doc.id, user.username)
    else:
        locked, locked_by = False, None

    return jingo.render(request, 'wiki/translate.html',
                        {'parent': parent_doc, 'document': doc,
                         'document_form': doc_form, 'revision_form': rev_form,
                         'locale': request.LANGUAGE_CODE, 'based_on': based_on_rev,
                         'disclose_description': disclose_description,
                         'show_revision_warning': show_revision_warning,
                         'recent_approved_revs': recent_approved_revs,
                         'locked': locked,
                         'locked_by': locked_by})


@require_POST
@login_required
def watch_document(request, document_slug):
    """Start watching a document for edits."""
    document = get_object_or_404(
        Document, locale=request.LANGUAGE_CODE, slug=document_slug)
    EditDocumentEvent.notify(request.user, document)
    statsd.incr('wiki.watches.document')
    return HttpResponseRedirect(document.get_absolute_url())


@require_POST
@login_required
def unwatch_document(request, document_slug):
    """Stop watching a document for edits."""
    document = get_object_or_404(
        Document, locale=request.LANGUAGE_CODE, slug=document_slug)
    EditDocumentEvent.stop_notifying(request.user, document)
    return HttpResponseRedirect(document.get_absolute_url())


@require_POST
@login_required
def watch_locale(request):
    """Start watching a locale for revisions ready for review."""
    ReviewableRevisionInLocaleEvent.notify(request.user, locale=request.LANGUAGE_CODE)
    statsd.incr('wiki.watches.locale')
    # A 200 so jQuery interprets it as success
    return HttpResponse()


@require_POST
@login_required
def unwatch_locale(request):
    """Stop watching a locale for revisions ready for review."""
    ReviewableRevisionInLocaleEvent.stop_notifying(request.user,
                                                   locale=request.LANGUAGE_CODE)
    return HttpResponse()


@require_POST
@login_required
def watch_approved(request):
    """Start watching approved revisions in a locale."""
    if request.LANGUAGE_CODE not in settings.SUMO_LANGUAGES:
        raise Http404
    ApproveRevisionInLocaleEvent.notify(request.user, locale=request.LANGUAGE_CODE)
    statsd.incr('wiki.watches.approved')
    return HttpResponse()


@require_POST
@login_required
def unwatch_approved(request):
    """Stop watching approved revisions."""
    if request.LANGUAGE_CODE not in settings.SUMO_LANGUAGES:
        raise Http404
    ApproveRevisionInLocaleEvent.stop_notifying(request.user,
                                                locale=request.LANGUAGE_CODE)
    return HttpResponse()


@require_POST
@login_required
def watch_ready(request):
    """Start watching ready-for-l10n revisions."""
    if request.LANGUAGE_CODE != settings.WIKI_DEFAULT_LANGUAGE:
        raise Http404
    ReadyRevisionEvent.notify(request.user)
    statsd.incr('wiki.watches.ready')
    return HttpResponse()


@require_POST
@login_required
def unwatch_ready(request):
    """Stop watching ready-for-l10n revisions."""
    if request.LANGUAGE_CODE != settings.WIKI_DEFAULT_LANGUAGE:
        raise Http404
    ReadyRevisionEvent.stop_notifying(request.user)
    return HttpResponse()


@require_GET
def json_view(request):
    """Return some basic document info in a JSON blob."""
    kwargs = {'locale': request.LANGUAGE_CODE, 'current_revision__isnull': False}
    if 'title' in request.GET:
        kwargs['title'] = request.GET['title']
    elif 'slug' in request.GET:
        kwargs['slug'] = request.GET['slug']
    else:
        return HttpResponseBadRequest()

    document = get_object_or_404(Document, **kwargs)
    data = json.dumps({
        'id': document.id,
        'locale': document.locale,
        'slug': document.slug,
        'title': document.title,
        'summary': document.current_revision.summary,
        'url': document.get_absolute_url(),
    })
    return HttpResponse(data, mimetype='application/json')


@require_POST
@csrf_exempt
def helpful_vote(request, document_slug):
    """Vote for Helpful/Not Helpful document"""
    if 'revision_id' not in request.POST:
        return HttpResponseBadRequest()

    revision = get_object_or_404(
        Revision, id=smart_int(request.POST['revision_id']))
    survey = None

    if revision.document.category == TEMPLATES_CATEGORY:
        return HttpResponseBadRequest()

    if not revision.has_voted(request):
        ua = request.META.get('HTTP_USER_AGENT', '')[:1000]  # 1000 max_length
        source = request.POST.get('source')
        vote = HelpfulVote(revision=revision, user_agent=ua)

        if 'helpful' in request.POST:
            vote.helpful = True
            message = _('Glad to hear it &mdash; thanks for the feedback!')
        else:
            message = _('Sorry to hear that.')

        if request.user.is_authenticated():
            vote.creator = request.user
        else:
            vote.anonymous_id = request.anonymous.anonymous_id

        vote.save()
        statsd.incr('wiki.vote')

        # Send a survey if flag is enabled and vote wasn't helpful.
        if 'helpful' not in request.POST:
            survey = jingo.render_to_string(
                request, 'wiki/includes/unhelpful_survey.html',
                {'vote_id': vote.id})

        # Save vote metadata: referrer and search query (if available)
        for name in ['referrer', 'query', 'source']:
            val = request.POST.get(name)
            if val:
                vote.add_metadata(name, val)
    else:
        message = _('You already voted on this Article.')

    if request.is_ajax():
        r = {'message': message}
        if survey:
            r.update(survey=survey)

        return HttpResponse(json.dumps(r))

    return HttpResponseRedirect(revision.document.get_absolute_url())


@require_POST
@csrf_exempt
def unhelpful_survey(request):
    """Ajax only view: Unhelpful vote survey processing."""
    vote = get_object_or_404(HelpfulVote,
                             id=smart_int(request.POST.get('vote_id')))

    # The survey is the posted data, minus the vote_id and button value.
    survey = request.POST.copy()
    survey.pop('vote_id')
    survey.pop('button')

    # Save the survey in JSON format, taking care not to exceed 1000 chars.
    vote.add_metadata('survey', truncated_json_dumps(survey, 1000, 'comment'))

    return HttpResponse(
        json.dumps({'message': _('Thanks for making us better!')}))


@require_GET
def get_helpful_votes_async(request, document_slug):
    document = get_object_or_404(
        Document, locale=request.LANGUAGE_CODE, slug=document_slug)

    yes_data = []
    no_data = []
    perc_data = []
    date_to_rev_id = {}
    date_tooltip = {}
    flag_data = []
    rev_data = []
    revisions = set([])
    created_list = []

    start = time.time()
    cursor = connection.cursor()

    cursor.execute('SELECT wiki_helpfulvote.revision_id, '
                             'SUM(wiki_helpfulvote.helpful), '
                             'SUM(NOT(wiki_helpfulvote.helpful)), '
                             'wiki_helpfulvote.created '
                        'FROM wiki_helpfulvote '
                        'INNER JOIN wiki_revision ON '
                            'wiki_helpfulvote.revision_id=wiki_revision.id '
                        'WHERE wiki_revision.document_id=%s '
                        'GROUP BY DATE(wiki_helpfulvote.created)',
                        [document.id])

    results = cursor.fetchall()
    for res in results:
        created = 1000 * (int(time.mktime(res[3].timetuple()) / 86400) * 86400)
        percent = float(res[1]) / (float(res[1]) + float(res[2]))
        yes_data.append({'x': created, 'y': int(res[1])})
        no_data.append({'x': created, 'y': int(res[2])})
        perc_data.append({'x': created, 'y': percent})
        date_to_rev_id[created] = res[0]
        date_tooltip[created] = {'yes': int(res[1]),
                                 'no': int(res[2]),
                                 'percent': round(percent * 100, 2)}
        revisions.add(int(res[0]))
        created_list.append(res[3])

    if created_list == []:
        send = {'data': [],
                'date_to_rev_id': [],
                'date_tooltip': [],
                'query': 0}

        return HttpResponse(json.dumps(send),
                        mimetype='application/json')

    min_created = min(created_list)
    max_created = max(created_list)

    for flag in ImportantDate.uncached.filter(date__gte=min_created,
                                             date__lte=max_created):
        flag_data.append({
            'x': 1000 * int(time.mktime(flag.date.timetuple())),
            'title': _(flag.text),
            'text': _(flag.text)
            #'url': 'http://www.google.com/'  # Not supported yet
        })

    for rev in Revision.objects.filter(pk__in=revisions,
                                       created__gte=min_created,
                                       created__lte=max_created):
        rdate = rev.reviewed or rev.created
        rev_data.append({
                    'x': 1000 * int(time.mktime(rdate.timetuple())),
                    # L10n: 'R' is the first letter of "Revision".
                    'title': _('R', 'revision_heading'),
                    'text': unicode(_('Revision %s')) % rev.created
                    #'url': 'http://www.google.com/'  # Not supported yet
                })

    end = time.time()

    send = {'data': [{'name': _('Yes'),
                      'id': 'yes_data',
                      'data': yes_data,
                      'yAxis': 1},
                     {'name': _('No'),
                      'id': 'no_data',
                      'data': no_data,
                      'yAxis': 1},
                     {'name': _('Helpfulness Percentage'),
                      'id': 'perc_data',
                      'data': perc_data},
                     {'type': 'flags',
                      'data': rev_data,
                      'shape': 'circlepin',
                      'width': 16,
                      'zIndex': 100,
                      'showInLegend': False,
                      'onSeries': 'perc_data'},
                     {'type': 'flags',
                      'data': flag_data,
                      'shape': 'squarepin',
                      'stickyTracking': False,
                      'zIndex': 50,
                      'showInLegend': False}],
            'date_to_rev_id': date_to_rev_id,
            'date_tooltip': date_tooltip,
            'query': round(end - start, 2)}

    if len(send['data'][3]['data']) == 0:
        send['data'].pop(3)
    if len(send['data'][2]['data']) == 0:
        send['data'].pop(2)
    if len(send['data'][1]['data']) == 0:
        send['data'].pop(1)
    if len(send['data'][0]['data']) == 0:
        send['data'].pop(0)

    return HttpResponse(json.dumps(send),
                        mimetype='application/json')


@login_required
@permission_required('wiki.delete_revision')
def delete_revision(request, document_slug, revision_id):
    """Delete a revision."""
    revision = get_object_or_404(Revision, pk=revision_id,
                                 document__slug=document_slug)
    document = revision.document
    only_revision = document.revisions.count() == 1
    helpful_votes = HelpfulVote.objects.filter(revision=revision.id)
    has_votes = helpful_votes.exists()

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'wiki/confirm_revision_delete.html',
                            {'revision': revision, 'document': document,
                             'only_revision': only_revision,
                             'has_votes': has_votes})

    # Don't delete the only revision of a document
    if only_revision:
        return HttpResponseBadRequest()

    log.warning('User %s is deleting revision with id=%s' %
                (request.user, revision.id))
    revision.delete()
    return HttpResponseRedirect(reverse('wiki.document_revisions',
                                        args=[document.slug]))


@login_required
@permission_required('wiki.mark_ready_for_l10n')
@require_POST
def mark_ready_for_l10n_revision(request, document_slug, revision_id):
    """Mark a revision as ready for l10n."""
    revision = get_object_or_404(Revision, pk=revision_id,
                                 document__slug=document_slug)

    if revision.can_be_readied_for_localization():
        # We don't use update(), because that wouldn't update
        # Document.latest_localizable_revision.
        revision.is_ready_for_localization = True
        revision.save()

        ReadyRevisionEvent(revision).fire(exclude=request.user)

        return HttpResponse(json.dumps({'message': revision_id}))

    return HttpResponseBadRequest()


@login_required
def delete_document(request, document_slug):
    """Delete a revision."""
    document = get_object_or_404(Document, locale=request.LANGUAGE_CODE,
                                 slug=document_slug)

    # Check permission
    if not document.allows_deleting_by(request.user):
        raise PermissionDenied

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'wiki/confirm_document_delete.html',
                            {'document': document})

    # Handle confirm delete form POST
    log.warning('User %s is deleting document: %s (id=%s)' %
                (request.user, document.title, document.id))
    document.delete()

    return jingo.render(request, 'wiki/confirm_document_delete.html',
                        {'document': document, 'delete_confirmed': True})


@login_required
@require_POST
@permission_required('wiki.change_document')
def add_contributor(request, document_slug):
    """Add a contributor to a document."""
    document = get_object_or_404(Document, locale=request.LANGUAGE_CODE,
                                 slug=document_slug)

    form = AddContributorForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data['users']:
            document.contributors.add(user)
        msg = _('{users} added to the contributors successfully!').format(
            users=request.POST.get('users'))
        messages.add_message(request, messages.SUCCESS, msg)

        return HttpResponseRedirect(reverse('wiki.document_revisions',
                                            args=[document_slug]))

    msg = _('There were errors adding new contributors, see below.')
    messages.add_message(request, messages.ERROR, msg)
    return document_revisions(request, document_slug, contributor_form=form)


@login_required
@require_http_methods(['GET', 'POST'])
@permission_required('wiki.change_document')
def remove_contributor(request, document_slug, user_id):
    """Remove a contributor from a document."""
    document = get_object_or_404(Document, locale=request.LANGUAGE_CODE,
                                 slug=document_slug)
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        document.contributors.remove(user)
        msg = _('{user} removed from the contributors successfully!').format(
                user=user.username)
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(reverse('wiki.document_revisions',
                                            args=[document_slug]))

    return jingo.render(request, 'wiki/confirm_remove_contributor.html',
                        {'document': document, 'contributor': user})

def show_translations(request, document_slug):
    document = get_object_or_404(
        Document, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug)
    translated_locales = []
    untranslated_locales = []

    translated_locales.append(document.locale)
    translated_locales.extend(document.translations.all().values_list(
        'locale', flat=True))

    for locale in settings.LANGUAGE_CHOICES:
        if not locale[0] in translated_locales:
            untranslated_locales.append(locale[0])

    return jingo.render(request, 'wiki/show_translations.html',
            {'document': document, 
            'translated_locales': translated_locales,
            'untranslated_locales': untranslated_locales})

def _document_form_initial(document):
    """Return a dict with the document data pertinent for the form."""
    return {'title': document.title,
            'slug': document.slug,
            'category': document.category,
            'is_localizable': document.is_localizable,
            'is_archived': document.is_archived,
            'topics': Topic.uncached.filter(
                document=document).values_list('id', flat=True),
            'products': Product.uncached.filter(
                document=document).values_list('id', flat=True),
            'allow_discussion': document.allow_discussion,
            'needs_change': document.needs_change,
            'needs_change_comment': document.needs_change_comment}


def _save_rev_and_notify(rev_form, creator, document, based_on_id=None):
    """Save the given RevisionForm and send notifications."""
    new_rev = rev_form.save(creator, document, based_on_id)
    statsd.incr('wiki.revision')

    # Enqueue notifications
    ReviewableRevisionInLocaleEvent(new_rev).fire(exclude=new_rev.creator)
    EditDocumentEvent(new_rev).fire(exclude=new_rev.creator)


def _maybe_schedule_rebuild(form):
    """Try to schedule a KB rebuild if a title or slug has changed."""
    if 'title' in form.changed_data or 'slug' in form.changed_data:
        schedule_rebuild_kb()


def _get_next_url_fallback_localization(request):
    return get_next_url(request) or reverse('dashboards.localization')


def _show_revision_warning(document, revision):
    if revision:
        return document.revisions.filter(created__gt=revision.created,
                                         reviewed=None).exists()
    return False
