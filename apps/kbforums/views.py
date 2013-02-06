import logging
from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

import jingo
from statsd import statsd

from access.decorators import permission_required, login_required
import kbforums
from kbforums.events import (NewPostEvent, NewThreadEvent,
                             NewPostInLocaleEvent, NewThreadInLocaleEvent)
from kbforums.feeds import ThreadsFeed, PostsFeed
from kbforums.forms import (ReplyForm, NewThreadForm,
                            EditThreadForm, EditPostForm)
from kbforums.models import Thread, Post
from sumo_locales import LOCALES
from sumo.urlresolvers import reverse
from sumo.utils import paginate, get_next_url
from users.models import Setting
from wiki.models import Document


log = logging.getLogger('k.kbforums')


def get_document(slug, request):
    """Given a slug and a request, get the document or 404."""
    return get_object_or_404(Document,
                             slug=slug,
                             locale=request.LANGUAGE_CODE,
                             allow_discussion=True)


def sort_threads(threads_, sort=0, desc=0):
    if desc:
        prefix = '-'
    else:
        prefix = ''

    if sort == 3:
        return threads_.order_by(prefix + 'creator__username').all()
    elif sort == 4:
        return threads_.order_by(prefix + 'replies').all()
    elif sort == 5:
        return threads_.order_by(prefix + 'last_post__created').all()

    # If nothing matches, use default sorting
    return threads_.all()


def threads(request, document_slug):
    """View all the threads in a discussion forum."""
    doc = get_document(document_slug, request)
    try:
        sort = int(request.GET.get('sort', 0))
    except ValueError:
        sort = 0

    try:
        desc = int(request.GET.get('desc', 0))
    except ValueError:
        desc = 0
    desc_toggle = 0 if desc else 1

    threads_ = sort_threads(doc.thread_set, sort, desc)
    threads_ = paginate(request, threads_,
                        per_page=kbforums.THREADS_PER_PAGE)

    feed_urls = ((reverse('wiki.discuss.threads.feed', args=[document_slug]),
                  ThreadsFeed().title(doc)),)

    is_watching_forum = (request.user.is_authenticated() and
                         NewThreadEvent.is_notifying(request.user, doc))
    return jingo.render(request, 'kbforums/threads.html',
                        {'document': doc, 'threads': threads_,
                         'is_watching_forum': is_watching_forum,
                         'sort': sort, 'desc_toggle': desc_toggle,
                         'feeds': feed_urls})


def posts(request, document_slug, thread_id, form=None, post_preview=None):
    """View all the posts in a thread."""
    doc = get_document(document_slug, request)

    thread = get_object_or_404(Thread, pk=thread_id, document=doc)

    posts_ = thread.post_set.all()
    count = posts_.count()
    if count:
        last_post = posts_[count - 1]
    else:
        last_post = None
    posts_ = paginate(request, posts_, kbforums.POSTS_PER_PAGE)

    if not form:
        form = ReplyForm()

    feed_urls = ((reverse('wiki.discuss.posts.feed',
                          kwargs={'document_slug': document_slug,
                                  'thread_id': thread_id}),
                  PostsFeed().title(thread)),)

    is_watching_thread = (request.user.is_authenticated() and
                          NewPostEvent.is_notifying(request.user, thread))
    return jingo.render(request, 'kbforums/posts.html',
                        {'document': doc, 'thread': thread,
                         'posts': posts_, 'form': form,
                         'count': count,
                         'last_post': last_post,
                         'post_preview': post_preview,
                         'is_watching_thread': is_watching_thread,
                         'feeds': feed_urls})


@login_required
@require_POST
def reply(request, document_slug, thread_id):
    """Reply to a thread."""
    doc = get_document(document_slug, request)

    form = ReplyForm(request.POST)
    post_preview = None
    if form.is_valid():
        thread = get_object_or_404(Thread, pk=thread_id, document=doc)

        if not thread.is_locked:
            reply_ = form.save(commit=False)
            reply_.thread = thread
            reply_.creator = request.user
            if 'preview' in request.POST:
                post_preview = reply_
            else:
                reply_.save()
                statsd.incr('kbforums.reply')

                # Subscribe the user to the thread.
                if Setting.get_for_user(request.user,
                                        'kbforums_watch_after_reply'):
                    NewPostEvent.notify(request.user, thread)

                # Send notifications to thread/forum watchers.
                NewPostEvent(reply_).fire(exclude=reply_.creator)

                return HttpResponseRedirect(reply_.get_absolute_url())

    return posts(request, document_slug, thread_id, form, post_preview)


@login_required
def new_thread(request, document_slug):
    """Start a new thread."""
    doc = get_document(document_slug, request)

    if request.method == 'GET':
        form = NewThreadForm()
        return jingo.render(request, 'kbforums/new_thread.html',
                            {'form': form, 'document': doc})

    form = NewThreadForm(request.POST)
    post_preview = None
    if form.is_valid():
        if 'preview' in request.POST:
            thread = Thread(creator=request.user,
                            title=form.cleaned_data['title'])
            post_preview = Post(thread=thread, creator=request.user,
                                content=form.cleaned_data['content'])
        else:
            thread = doc.thread_set.create(creator=request.user,
                                             title=form.cleaned_data['title'])
            thread.save()
            statsd.incr('kbforums.thread')
            post = thread.new_post(creator=request.user,
                                   content=form.cleaned_data['content'])
            post.save()

            # Send notifications to forum watchers.
            NewThreadEvent(post).fire(exclude=post.creator)

            # Add notification automatically if needed.
            if Setting.get_for_user(request.user, 'kbforums_watch_new_thread'):
                NewPostEvent.notify(request.user, thread)

            return HttpResponseRedirect(
                reverse('wiki.discuss.posts', args=[document_slug, thread.id]))

    return jingo.render(request, 'kbforums/new_thread.html',
                        {'form': form, 'document': doc,
                         'post_preview': post_preview})


@require_POST
@permission_required('kbforums.lock_thread')
def lock_thread(request, document_slug, thread_id):
    """Lock/Unlock a thread."""
    doc = get_document(document_slug, request)
    thread = get_object_or_404(Thread, pk=thread_id, document=doc)
    thread.is_locked = not thread.is_locked
    log.info("User %s set is_locked=%s on KB thread with id=%s " %
             (request.user, thread.is_locked, thread.id))
    thread.save()

    return HttpResponseRedirect(
        reverse('wiki.discuss.posts', args=[document_slug, thread_id]))


@require_POST
@permission_required('kbforums.sticky_thread')
def sticky_thread(request, document_slug, thread_id):
    """Mark/unmark a thread sticky."""
    doc = get_document(document_slug, request)
    thread = get_object_or_404(Thread, pk=thread_id, document=doc)
    thread.is_sticky = not thread.is_sticky
    log.info("User %s set is_sticky=%s on KB thread with id=%s " %
             (request.user, thread.is_sticky, thread.id))
    thread.save()

    return HttpResponseRedirect(
        reverse('wiki.discuss.posts', args=[document_slug, thread_id]))


@login_required
def edit_thread(request, document_slug, thread_id):
    """Edit a thread."""
    doc = get_document(document_slug, request)
    thread = get_object_or_404(Thread, pk=thread_id, document=doc)

    perm = request.user.has_perm('kbforums.change_thread')
    if not (perm or (thread.creator == request.user and
                     not thread.is_locked)):
        raise PermissionDenied

    if request.method == 'GET':
        form = EditThreadForm(instance=thread)
        return jingo.render(request, 'kbforums/edit_thread.html',
                            {'form': form, 'document': doc, 'thread': thread})

    form = EditThreadForm(request.POST)

    if form.is_valid():
        log.warning('User %s is editing KB thread with id=%s' %
                    (request.user, thread.id))
        thread.title = form.cleaned_data['title']
        thread.save()

        url = reverse('wiki.discuss.posts', args=[document_slug, thread_id])
        return HttpResponseRedirect(url)

    return jingo.render(request, 'kbforums/edit_thread.html',
                        {'form': form, 'document': doc, 'thread': thread})


@permission_required('kbforums.delete_thread')
def delete_thread(request, document_slug, thread_id):
    """Delete a thread."""
    doc = get_document(document_slug, request)
    thread = get_object_or_404(Thread, pk=thread_id, document=doc)

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'kbforums/confirm_thread_delete.html',
                            {'document': doc, 'thread': thread})

    # Handle confirm delete form POST
    log.warning('User %s is deleting KB thread with id=%s' %
                (request.user, thread.id))
    thread.delete()

    return HttpResponseRedirect(reverse('wiki.discuss.threads',
                                        args=[document_slug]))


@login_required
def edit_post(request, document_slug, thread_id, post_id):
    """Edit a post."""
    doc = get_document(document_slug, request)
    thread = get_object_or_404(Thread, pk=thread_id, document=doc)
    post = get_object_or_404(Post, pk=post_id, thread=thread)

    perm = request.user.has_perm('kbforums.change_post')
    if not (perm or (request.user == post.creator and not thread.is_locked)):
        raise PermissionDenied

    if request.method == 'GET':
        form = EditPostForm({'content': post.content})
        return jingo.render(request, 'kbforums/edit_post.html',
                            {'form': form, 'document': doc,
                             'thread': thread, 'post': post})

    form = EditPostForm(request.POST)
    post_preview = None
    if form.is_valid():
        post.content = form.cleaned_data['content']
        post.updated_by = request.user
        if 'preview' in request.POST:
            post.updated = datetime.now()
            post_preview = post
        else:
            log.warning('User %s is editing KB post with id=%s' %
                        (request.user, post.id))
            post.save()
            return HttpResponseRedirect(post.get_absolute_url())

    return jingo.render(request, 'kbforums/edit_post.html',
                        {'form': form, 'document': doc,
                         'thread': thread, 'post': post,
                         'post_preview': post_preview})


@permission_required('kbforums.delete_post')
def delete_post(request, document_slug, thread_id, post_id):
    """Delete a post."""
    doc = get_document(document_slug, request)
    thread = get_object_or_404(Thread, pk=thread_id, document=doc)
    post = get_object_or_404(Post, pk=post_id, thread=thread)

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'kbforums/confirm_post_delete.html',
                            {'document': doc, 'thread': thread, 'post': post})

    # Handle confirm delete form POST
    log.warning("User %s is deleting KB post with id=%s" %
                (request.user, post.id))
    post.delete()
    try:
        Thread.objects.get(pk=thread_id)
        goto = reverse('wiki.discuss.posts',
                       args=[document_slug, thread_id])
    except Thread.DoesNotExist:
        # The thread was deleted, go to the threads list page
        goto = reverse('wiki.discuss.threads', args=[document_slug])

    return HttpResponseRedirect(goto)


@require_POST
@login_required
def watch_thread(request, document_slug, thread_id):
    """Watch/unwatch a thread (based on 'watch' POST param)."""
    doc = get_document(document_slug, request)
    thread = get_object_or_404(Thread, pk=thread_id, document=doc)

    if request.POST.get('watch') == 'yes':
        NewPostEvent.notify(request.user, thread)
        statsd.incr('kbforums.watches.thread')
    else:
        NewPostEvent.stop_notifying(request.user, thread)

    return HttpResponseRedirect(reverse('wiki.discuss.posts',
                                        args=[document_slug, thread_id]))


@require_POST
@login_required
def watch_locale(request):
    """Watch/unwatch a locale."""
    locale = request.LANGUAGE_CODE
    if request.POST.get('watch') == 'yes':
        NewPostInLocaleEvent.notify(request.user, locale=locale)
        NewThreadInLocaleEvent.notify(request.user, locale=locale)
        statsd.incr('kbforums.watches.locale')
    else:
        NewPostInLocaleEvent.stop_notifying(request.user, locale=locale)
        NewThreadInLocaleEvent.stop_notifying(request.user, locale=locale)

    # If there is no next url, send the user to the home page.
    return HttpResponseRedirect(get_next_url(request) or reverse('home'))


@require_POST
@login_required
def watch_forum(request, document_slug):
    """Watch/unwatch a document (based on 'watch' POST param)."""
    doc = get_document(document_slug, request)
    if request.POST.get('watch') == 'yes':
        NewThreadEvent.notify(request.user, doc)
        statsd.incr('kbforums.watches.document')
    else:
        NewThreadEvent.stop_notifying(request.user, doc)

    return HttpResponseRedirect(reverse('wiki.discuss.threads',
                                        args=[document_slug]))


@require_POST
@login_required
def post_preview_async(request, document_slug):
    """Ajax preview of posts."""
    statsd.incr('forums.preview')
    post = Post(creator=request.user, content=request.POST.get('content', ''))
    return jingo.render(request, 'kbforums/includes/post_preview.html',
                        {'post_preview': post})


def locale_discussions(request):
    locale_name = LOCALES[request.LANGUAGE_CODE].native
    threads = Thread.objects.filter(document__locale=request.LANGUAGE_CODE,
                                    document__allow_discussion=True)
    try:
        sort = int(request.GET.get('sort', 0))
    except ValueError:
        sort = 0

    try:
        desc = int(request.GET.get('desc', 0))
    except ValueError:
        desc = 0
    desc_toggle = 0 if desc else 1

    threads_ = sort_threads(threads, sort, desc)

    # Ignore sticky-ness:
    threads_ = threads_.order_by('-last_post__created')
    threads_ = paginate(request, threads_,
                        per_page=kbforums.THREADS_PER_PAGE)
    is_watching_locale = (request.user.is_authenticated() and
                          NewThreadInLocaleEvent.is_notifying(
                            request.user, locale=request.LANGUAGE_CODE))
    return jingo.render(request, 'kbforums/discussions.html',
                        {'locale_name': locale_name, 'threads': threads_,
                         'desc_toggle': desc_toggle,
                         'is_watching_locale': is_watching_locale})
