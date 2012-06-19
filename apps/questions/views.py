from datetime import date, datetime, timedelta
import json
import logging
import random

from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import (HttpResponseRedirect, HttpResponse, Http404,
                         HttpResponseBadRequest, HttpResponseForbidden)
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (require_POST, require_GET,
                                          require_http_methods)

import jingo
from mobility.decorators import mobile_template
from session_csrf import anonymous_csrf
from statsd import statsd
from taggit.models import Tag
from tidings.events import ActivationRequestFailed
from tidings.models import Watch
from tower import ugettext as _, ugettext_lazy as _lazy
import waffle

from access.decorators import (has_perm_or_owns_or_403, permission_required,
                               login_required)
from karma.manager import KarmaManager
import questions as constants
from questions.events import QuestionReplyEvent, QuestionSolvedEvent
from questions.feeds import QuestionsFeed, AnswersFeed, TaggedQuestionsFeed
from questions.forms import (NewQuestionForm, EditQuestionForm, AnswerForm,
                             WatchQuestionForm, FREQUENCY_CHOICES,
                             MarketplaceAaqForm)
from questions.karma_actions import (SolutionAction, AnswerMarkedHelpfulAction,
                                     AnswerMarkedNotHelpfulAction)
from questions.marketplace import (MARKETPLACE_CATEGORIES, submit_ticket,
                                   ZendeskError)
from questions.models import (Question, Answer, QuestionVote, AnswerVote,
                              question_searcher)
from questions.question_config import products
from search.utils import locale_or_default, clean_excerpt
from search.es_utils import ESTimeoutError, ESMaxRetryError, ESException
from search import SearchError
from sumo.helpers import urlparams
from sumo.urlresolvers import reverse
from sumo.utils import paginate, simple_paginate, build_paged_url
from tags.utils import add_existing_tag
from upload.models import ImageAttachment
from upload.views import upload_imageattachment
from users.forms import RegisterForm
from users.models import Setting
from users.utils import handle_login, handle_register
from wiki.models import Document, wiki_searcher


log = logging.getLogger('k.questions')


UNAPPROVED_TAG = _lazy(u'That tag does not exist.')
NO_TAG = _lazy(u'Please provide a tag.')


def questions(request):
    """View the questions."""

    filter_ = request.GET.get('filter')
    tagged = request.GET.get('tagged')
    tags = None
    sort_ = request.GET.get('sort', None)

    if sort_ == 'requested':
        order = '-num_votes_past_week'
    elif sort_ == 'created':
        order = '-created'
    else:
        order = '-updated'

    question_qs = Question.objects.select_related(
        'creator', 'last_answer', 'last_answer__creator')
    question_qs = question_qs.extra(
        {'_num_votes': 'SELECT COUNT(*) FROM questions_questionvote WHERE '
                       'questions_questionvote.question_id = '
                       'questions_question.id'})
    question_qs = question_qs.filter(creator__is_active=1)

    if filter_ == 'no-replies':
        question_qs = question_qs.filter(num_answers=0, is_locked=False)
    elif filter_ == 'replies':
        question_qs = question_qs.filter(num_answers__gt=0)
    elif filter_ == 'solved':
        question_qs = question_qs.exclude(solution=None)
    elif filter_ == 'unsolved':
        question_qs = question_qs.filter(solution=None)
    elif filter_ == 'my-contributions' and request.user.is_authenticated():
        criteria = Q(answers__creator=request.user) | Q(creator=request.user)
        question_qs = question_qs.filter(criteria).distinct()
    elif filter_ == 'recent-unanswered':
        # Only unanswered questions from the last 72 hours.
        start = datetime.now() - timedelta(hours=72)
        question_qs = question_qs.filter(
            num_answers=0, created__gt=start, is_locked=False)
    else:
        filter_ = None

    feed_urls = ((reverse('questions.feed'),
                  QuestionsFeed().title()),)

    if tagged:
        tag_slugs = tagged.split(',')
        tags = Tag.objects.filter(slug__in=tag_slugs)
        if tags:
            for t in tags:
                question_qs = question_qs.filter(tags__name__in=[t.name])
            if len(tags) == 1:
                feed_urls += ((reverse('questions.tagged_feed',
                                       args=[tags[0].slug]),
                               TaggedQuestionsFeed().title(tags[0])),)
        else:
            question_qs = Question.objects.get_empty_query_set()

    # Exclude questions over 90 days old without an answer.
    oldest_date = date.today() - timedelta(days=90)
    question_qs = question_qs.exclude(created__lt=oldest_date, num_answers=0)

    # Set the order.
    question_qs = question_qs.order_by(order)

    try:
        with statsd.timer('questions.view.paginate.%s' % filter_):
            questions_page = simple_paginate(
                request, question_qs, per_page=constants.QUESTIONS_PER_PAGE)
    except (PageNotAnInteger, EmptyPage):
        # If we aren't on page 1, redirect there.
        # TODO: Is 404 more appropriate?
        if request.GET.get('page', '1') != '1':
            url = build_paged_url(request)
            return HttpResponseRedirect(urlparams(url, page=1))

    # Recent answered stats
    recent_asked_count = Question.recent_asked_count()
    recent_unanswered_count = Question.recent_unanswered_count()
    if recent_asked_count:
        recent_answered_percent = int(
            (float(recent_asked_count - recent_unanswered_count) /
            recent_asked_count) * 100)
    else:
        recent_answered_percent = 0

    data = {'questions': questions_page,
            'feeds': feed_urls,
            'filter': filter_,
            'sort': sort_,
            'tags': tags,
            'tagged': tagged,
            'recent_asked_count': recent_asked_count,
            'recent_unanswered_count': recent_unanswered_count,
            'recent_answered_percent': recent_answered_percent}

    if (waffle.flag_is_active(request, 'karma') and
        waffle.switch_is_active('karma')):
        kmgr = KarmaManager()
        data.update(karma_top=kmgr.top_users())
        if request.user.is_authenticated():
            ranking = kmgr.ranking(request.user)
            if ranking <= constants.HIGHEST_RANKING:
                data.update(karma_ranking=ranking)
    else:
        data.update(top_contributors=_get_top_contributors())

    with statsd.timer('questions.view.render'):
        return jingo.render(request, 'questions/questions.html', data)


@anonymous_csrf  # Need this so the anon csrf gets set for watch forms.
def answers(request, question_id, form=None, watch_form=None,
            answer_preview=None, **extra_kwargs):
    """View the answers to a question."""
    ans_ = _answers_data(request, question_id, form, watch_form,
                         answer_preview)
    question = ans_['question']

    if request.user.is_authenticated():
        ans_['images'] = question.images.filter(creator=request.user)

    extra_kwargs.update(ans_)

    # Add noindex to questions without answers that are > 30 days old.
    no_answers = ans_['answers'].paginator.count == 0
    if no_answers and question.created < datetime.now() - timedelta(days=30):
        extra_kwargs.update(robots_noindex=True)

    return jingo.render(request, 'questions/answers.html', extra_kwargs)


@mobile_template('questions/{mobile/}new_question.html')
@anonymous_csrf  # This view renders a login form
def aaq(request, product_key=None, category_key=None, showform=False,
        template=None, step=0):
    """Ask a new question."""

    if product_key is None:
        product_key = request.GET.get('product')
    product = products.get(product_key)
    if product_key and not product:
        raise Http404

    if category_key is None:
        category_key = request.GET.get('category')

    if product and category_key:
        category = product['categories'].get(category_key)
        if not category:
            raise Http404
        deadend = category.get('deadend', False)
        html = category.get('html')
        articles = category.get('articles')
    else:
        category = None
        deadend = product.get('deadend', False) if product else False
        html = product.get('html') if product else None
        articles = None
        if product:
            # User is on the select category step
            statsd.incr('questions.aaq.select-category')
        else:
            # User is on the select product step
            statsd.incr('questions.aaq.select-product')

    login_t = ('questions/mobile/new_question_login.html' if request.MOBILE
               else 'questions/new_question_login.html')
    if request.method == 'GET':
        search = request.GET.get('search', '')
        if search:
            try:
                results = _search_suggestions(
                    request,
                    search,
                    locale_or_default(request.locale),
                    product.get('tags'))
            except SearchError:
                # Just quietly advance the user to the next step.
                results = []
            tried_search = True
        else:
            results = []
            tried_search = False
            if category:
                # User is on the "Ask This" step
                statsd.incr('questions.aaq.search-form')

        if showform or request.GET.get('showform'):
            # Before we show the form, make sure the user is auth'd:
            if not request.user.is_authenticated():
                # User is on the login or register Step
                statsd.incr('questions.aaq.login-or-register')
                login_form = AuthenticationForm()
                register_form = RegisterForm()
                return jingo.render(request, login_t,
                                    {'product': product, 'category': category,
                                     'title': search,
                                     'register_form': register_form,
                                     'login_form': login_form})
            form = NewQuestionForm(product=product,
                                   category=category,
                                   initial={'title': search})
            # User is on the question details step
            statsd.incr('questions.aaq.details-form')
        else:
            form = None
            if search:
                # User is on the article and questions suggestions step
                statsd.incr('questions.aaq.suggestions')

        return jingo.render(request, template,
                            {'form': form,
                             'results': results,
                             'tried_search': tried_search,
                             'products': products,
                             'current_product': product,
                             'current_category': category,
                             'current_html': html,
                             'current_articles': articles,
                             'current_step': step,
                             'deadend': deadend,
                             'host': Site.objects.get_current().domain})

    # Handle the form post.
    if not request.user.is_authenticated():
        if request.POST.get('login'):
            login_form = handle_login(request, only_active=False)
            statsd.incr('questions.user.login')
            register_form = RegisterForm()
        elif request.POST.get('register'):
            login_form = AuthenticationForm()
            email_template = 'questions/email/confirm_question.ltxt'
            email_subject = _('Please confirm your Firefox Help question')
            email_data = request.GET.get('search')
            register_form = handle_register(request, email_template,
                                            email_subject, email_data)
            if register_form.is_valid():  # Now try to log in.
                user = auth.authenticate(username=request.POST.get('username'),
                                         password=request.POST.get('password'))
                auth.login(request, user)
                statsd.incr('questions.user.register')
        else:
            # L10n: This shouldn't happen unless people tamper with POST data.
            message = _lazy('Request type not recognized.')
            return jingo.render(request, 'handlers/400.html',
                            {'message': message}, status=400)
        if request.user.is_authenticated():
            # Redirect to GET the current URL.
            # This is required for the csrf middleware to set the auth'd tokens
            # appropriately.
            return HttpResponseRedirect(request.get_full_path())
        else:
            return jingo.render(request, login_t,
                                {'product': product, 'category': category,
                                 'title': request.POST.get('title'),
                                 'register_form': register_form,
                                 'login_form': login_form})

    form = NewQuestionForm(product=product, category=category,
                           data=request.POST)

    if form.is_valid():
        question = Question(creator=request.user,
                            title=form.cleaned_data['title'],
                            content=form.cleaned_data['content'])
        question.save()
        # User successfully submitted a new question
        statsd.incr('questions.new')
        question.add_metadata(**form.cleaned_metadata)
        if product:
            question.add_metadata(product=product['key'])
            if category:
                question.add_metadata(category=category['key'])

        # The first time a question is saved, automatically apply some tags:
        question.auto_tag()

        # Submitting the question counts as a vote
        question_vote(request, question.id)

        if request.user.is_active:
            messages.add_message(request, messages.SUCCESS,
                _('Done! Your question is now posted on the Mozilla community support forum.'))
            url = reverse('questions.answers',
                          kwargs={'question_id': question.id})
            return HttpResponseRedirect(url)

        auth.logout(request)
        statsd.incr('questions.user.logout')
        confirm_t = ('questions/mobile/confirm_email.html' if request.MOBILE
                     else 'questions/confirm_email.html')
        return jingo.render(request, confirm_t,
                            {'question': question})

    statsd.incr('questions.aaq.details-form-error')
    return jingo.render(request, template,
                        {'form': form, 'products': products,
                         'current_product': product,
                         'current_category': category,
                         'current_articles': articles})


def aaq_step2(request, product_key):
    """Step 2: The product is selected."""
    return aaq(request, product_key=product_key, step=1)


def aaq_step3(request, product_key, category_key):
    """Step 3: The product and category is selected."""
    return aaq(request, product_key=product_key, category_key=category_key, step=1)


def aaq_step4(request, product_key, category_key):
    """Step 4: Search query entered."""
    return aaq(request, product_key=product_key, category_key=category_key, step=1)


def aaq_step5(request, product_key, category_key):
    """Step 5: Show full question form."""
    return aaq(request, product_key=product_key, category_key=category_key,
               showform=True, step=3)


@require_http_methods(['GET', 'POST'])
@login_required
@has_perm_or_owns_or_403('questions.change_question', 'creator',
                         (Question, 'id__exact', 'question_id'),
                         (Question, 'id__exact', 'question_id'))
def edit_question(request, question_id):
    """Edit a question."""
    question = get_object_or_404(Question, pk=question_id)
    user = request.user

    if not user.has_perm('questions.change_question') and question.is_locked:
        raise PermissionDenied

    if request.method == 'GET':
        initial = question.metadata.copy()
        initial.update(title=question.title, content=question.content)
        form = EditQuestionForm(product=question.product,
                                category=question.category,
                                initial=initial)
    else:
        form = EditQuestionForm(data=request.POST,
                                product=question.product,
                                category=question.category)
        if form.is_valid():
            question.title = form.cleaned_data['title']
            question.content = form.cleaned_data['content']
            question.updated_by = user
            question.save()

            # TODO: Factor all this stuff up from here and new_question into
            # the form, which should probably become a ModelForm.
            question.clear_mutable_metadata()
            question.add_metadata(**form.cleaned_metadata)

            return HttpResponseRedirect(reverse('questions.answers',
                                        kwargs={'question_id': question.id}))

    return jingo.render(request, 'questions/edit_question.html',
                        {'question': question,
                         'form': form,
                         'current_product': question.product,
                         'current_category': question.category})


@require_POST
@login_required
def reply(request, question_id):
    """Post a new answer to a question."""
    question = get_object_or_404(Question, pk=question_id)
    answer_preview = None
    if question.is_locked:
        raise PermissionDenied

    form = AnswerForm(request.POST)

    # NOJS: delete images
    if 'delete_images' in request.POST:
        for image_id in request.POST.getlist('delete_image'):
            ImageAttachment.objects.get(pk=image_id).delete()

        return answers(request, question_id, form)

    # NOJS: upload image
    if 'upload_image' in request.POST:
        upload_imageattachment(request, question)
        return answers(request, question_id, form)

    if form.is_valid():
        answer = Answer(question=question, creator=request.user,
                        content=form.cleaned_data['content'])
        if 'preview' in request.POST:
            answer_preview = answer
        else:
            answer.save()
            ct = ContentType.objects.get_for_model(answer)
            # Move over to the answer all of the images I added to the
            # reply form
            up_images = question.images.filter(creator=request.user)
            up_images.update(content_type=ct, object_id=answer.id)
            statsd.incr('questions.answer')

            if Setting.get_for_user(request.user,
                                    'questions_watch_after_reply'):
                QuestionReplyEvent.notify(request.user, question)

            return HttpResponseRedirect(answer.get_absolute_url())

    return answers(request, question_id, form, answer_preview=answer_preview)


def solve(request, question_id, answer_id):
    """Accept an answer as the solution to the question."""

    question = get_object_or_404(Question, pk=question_id)

    # It is possible this was clicked from the email.
    if not request.user.is_authenticated():
        watch_secret = request.GET.get('watch', None)
        try:
            watch = Watch.objects.get(secret=watch_secret,
                                      event_type='question reply',
                                      user=question.creator)
            # Create a new secret.
            distinguishable_letters = \
                'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRTUVWXYZ'
            new_secret = ''.join(random.choice(distinguishable_letters)
                             for x in xrange(10))
            watch.update(secret=new_secret)
            request.user = question.creator
        except Watch.DoesNotExist:
            # This user is neither authenticated nor using the correct secret
            return HttpResponseForbidden()

    answer = get_object_or_404(Answer, pk=answer_id)
    if question.is_locked:
        raise PermissionDenied

    if (question.creator != request.user and
        not request.user.has_perm('questions.change_solution')):
        return HttpResponseForbidden()

    question.solution = answer
    question.save()

    statsd.incr('questions.solution')
    QuestionSolvedEvent(answer).fire(exclude=question.creator)
    SolutionAction(user=answer.creator, day=answer.created).save()

    messages.add_message(request, messages.SUCCESS,
                         _('Thank you for choosing a solution!'))

    return HttpResponseRedirect(question.get_absolute_url())


@require_POST
@login_required
def unsolve(request, question_id, answer_id):
    """Accept an answer as the solution to the question."""
    question = get_object_or_404(Question, pk=question_id)
    answer = get_object_or_404(Answer, pk=answer_id)
    if question.is_locked:
        raise PermissionDenied

    if (question.creator != request.user and
        not request.user.has_perm('questions.change_solution')):
        return HttpResponseForbidden()

    question.solution = None
    question.save()

    statsd.incr('questions.unsolve')
    SolutionAction(user=answer.creator, day=answer.created).delete()

    messages.add_message(request, messages.SUCCESS,
                         _("The solution was undone successfully."))

    return HttpResponseRedirect(question.get_absolute_url())


@require_POST
@csrf_exempt
def question_vote(request, question_id):
    """I have this problem too."""
    question = get_object_or_404(Question, pk=question_id)
    if question.is_locked:
        raise PermissionDenied

    if not question.has_voted(request):
        vote = QuestionVote(question=question)

        if request.user.is_authenticated():
            vote.creator = request.user
        else:
            vote.anonymous_id = request.anonymous.anonymous_id

        vote.save()
        ua = request.META.get('HTTP_USER_AGENT')
        if ua:
            vote.add_metadata('ua', ua[:1000])  # 1000 max_length
        statsd.incr('questions.votes.question')

        if request.is_ajax():
            tmpl = 'questions/includes/question_vote_thanks.html'
            form = _init_watch_form(request)
            html = jingo.render_to_string(request, tmpl, {'question': question,
                                                          'watch_form': form})
            return HttpResponse(json.dumps({'html': html}))

    return HttpResponseRedirect(question.get_absolute_url())


@csrf_exempt
def answer_vote(request, question_id, answer_id):
    """Vote for Helpful/Not Helpful answers"""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)
    if answer.question.is_locked:
        raise PermissionDenied

    if not answer.has_voted(request):
        vote = AnswerVote(answer=answer)

        if 'helpful' in request.REQUEST:
            vote.helpful = True
            AnswerMarkedHelpfulAction(answer.creator).save()
            message = _('Glad to hear it!')
        else:
            AnswerMarkedNotHelpfulAction(answer.creator).save()
            message = _('Sorry to hear that.')

        if request.user.is_authenticated():
            vote.creator = request.user
        else:
            vote.anonymous_id = request.anonymous.anonymous_id

        vote.save()
        ua = request.META.get('HTTP_USER_AGENT')
        if ua:
            vote.add_metadata('ua', ua[:1000])  # 1000 max_length
        statsd.incr('questions.votes.answer')
    else:
        message = _('You already voted on this reply.')

    if request.is_ajax():
        return HttpResponse(json.dumps({'message': message}))

    return HttpResponseRedirect(answer.get_absolute_url())


@permission_required('questions.tag_question')
def add_tag(request, question_id):
    """Add a (case-insensitive) tag to question.

    If the question already has the tag, do nothing.

    """
    # If somebody hits Return in the address bar after provoking an error from
    # the add form, nicely send them back to the question:
    if request.method == 'GET':
        return HttpResponseRedirect(
            reverse('questions.answers', args=[question_id]))

    try:
        question, canonical_name = _add_tag(request, question_id)
    except Tag.DoesNotExist:
        template_data = _answers_data(request, question_id)
        template_data['tag_adding_error'] = UNAPPROVED_TAG
        template_data['tag_adding_value'] = request.POST.get('tag-name', '')
        return jingo.render(request, 'questions/answers.html', template_data)

    if canonical_name:  # success
        question.clear_cached_tags()
        return HttpResponseRedirect(
            reverse('questions.answers', args=[question_id]))

    # No tag provided
    template_data = _answers_data(request, question_id)
    template_data['tag_adding_error'] = NO_TAG
    return jingo.render(request, 'questions/answers.html', template_data)


@permission_required('questions.tag_question')
@require_POST
def add_tag_async(request, question_id):
    """Add a (case-insensitive) tag to question asyncronously. Return empty.

    If the question already has the tag, do nothing.

    """
    try:
        question, canonical_name = _add_tag(request, question_id)
    except Tag.DoesNotExist:
        return HttpResponse(json.dumps({'error': unicode(UNAPPROVED_TAG)}),
                            mimetype='application/json',
                            status=400)

    if canonical_name:
        question.clear_cached_tags()
        tag = Tag.objects.get(name=canonical_name)
        tag_url = urlparams(reverse('questions.questions'), tagged=tag.slug)
        data = {'canonicalName': canonical_name,
                'tagUrl': tag_url}
        return HttpResponse(json.dumps(data),
                            mimetype='application/json')

    return HttpResponse(json.dumps({'error': unicode(NO_TAG)}),
                        mimetype='application/json',
                        status=400)


@permission_required('questions.tag_question')
@require_POST
def remove_tag(request, question_id):
    """Remove a (case-insensitive) tag from question.

    Expects a POST with the tag name embedded in a field name, like
    remove-tag-tagNameHere. If question doesn't have that tag, do nothing.

    """
    prefix = 'remove-tag-'
    names = [k for k in request.POST if k.startswith(prefix)]
    if names:
        name = names[0][len(prefix):]
        question = get_object_or_404(Question, pk=question_id)
        question.tags.remove(name)
        question.clear_cached_tags()

    return HttpResponseRedirect(
        reverse('questions.answers', args=[question_id]))


@permission_required('questions.tag_question')
@require_POST
def remove_tag_async(request, question_id):
    """Remove a (case-insensitive) tag from question.

    If question doesn't have that tag, do nothing. Return value is JSON.

    """
    name = request.POST.get('name')
    if name:
        question = get_object_or_404(Question, pk=question_id)
        question.tags.remove(name)
        question.clear_cached_tags()
        return HttpResponse('{}', mimetype='application/json')

    return HttpResponseBadRequest(json.dumps({'error': unicode(NO_TAG)}),
                                  mimetype='application/json')


@login_required
@permission_required('questions.delete_question')
def delete_question(request, question_id):
    """Delete a question"""
    question = get_object_or_404(Question, pk=question_id)

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'questions/confirm_question_delete.html',
                            {'question': question})

    # Handle confirm delete form POST
    log.warning('User %s is deleting question with id=%s' %
                (request.user, question.id))
    question.delete()

    return HttpResponseRedirect(reverse('questions.questions'))


@login_required
@permission_required('questions.delete_answer')
def delete_answer(request, question_id, answer_id):
    """Delete an answer"""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'questions/confirm_answer_delete.html',
                            {'answer': answer})

    # Handle confirm delete form POST
    log.warning('User %s is deleting answer with id=%s' %
                (request.user, answer.id))
    answer.delete()

    return HttpResponseRedirect(reverse('questions.answers',
                                args=[question_id]))


@require_POST
@login_required
@permission_required('questions.lock_question')
def lock_question(request, question_id):
    """Lock a question"""
    question = get_object_or_404(Question, pk=question_id)
    question.is_locked = not question.is_locked
    log.info("User %s set is_locked=%s on question with id=%s " %
             (request.user, question.is_locked, question.id))
    question.save()

    return HttpResponseRedirect(question.get_absolute_url())


@login_required
@has_perm_or_owns_or_403('questions.change_answer', 'creator',
                         (Answer, 'id__iexact', 'answer_id'),
                         (Answer, 'id__iexact', 'answer_id'))
def edit_answer(request, question_id, answer_id):
    """Edit an answer."""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)
    answer_preview = None
    if answer.question.is_locked:
        raise PermissionDenied

    # NOJS: upload images, if any
    upload_imageattachment(request, answer)

    if request.method == 'GET':
        form = AnswerForm({'content': answer.content})
        return jingo.render(request, 'questions/edit_answer.html',
                            {'form': form, 'answer': answer})

    form = AnswerForm(request.POST)

    if form.is_valid():
        answer.content = form.cleaned_data['content']
        answer.updated_by = request.user
        if 'preview' in request.POST:
            answer.updated = datetime.now()
            answer_preview = answer
        else:
            log.warning('User %s is editing answer with id=%s' %
                        (request.user, answer.id))
            answer.save()
            return HttpResponseRedirect(answer.get_absolute_url())

    return jingo.render(request, 'questions/edit_answer.html',
                        {'form': form, 'answer': answer,
                         'answer_preview': answer_preview})


@require_POST
@anonymous_csrf
def watch_question(request, question_id):
    """Start watching a question for replies or solution."""

    question = get_object_or_404(Question, pk=question_id)
    form = WatchQuestionForm(request.user, request.POST)

    # Process the form
    msg = None
    if form.is_valid():
        user_or_email = (request.user if request.user.is_authenticated()
                                      else form.cleaned_data['email'])
        try:
            if form.cleaned_data['event_type'] == 'reply':
                QuestionReplyEvent.notify(user_or_email, question)
            else:
                QuestionSolvedEvent.notify(user_or_email, question)
            statsd.incr('questions.watches.new')
        except ActivationRequestFailed:
            msg = _('Could not send a message to that email address.')

    # Respond to ajax request
    if request.is_ajax():
        if form.is_valid():
            msg = msg or (_('You will be notified of updates by email.') if
                              request.user.is_authenticated() else
                          _('You should receive an email shortly '
                            'to confirm your subscription.'))
            return HttpResponse(json.dumps({'message': msg}))

        if request.POST.get('from_vote'):
            tmpl = 'questions/includes/question_vote_thanks.html'
        else:
            tmpl = 'questions/includes/email_subscribe.html'

        html = jingo.render_to_string(request, tmpl, {'question': question,
                                                      'watch_form': form})
        return HttpResponse(json.dumps({'html': html}))

    if msg:
        messages.add_message(request, messages.ERROR, msg)

    return HttpResponseRedirect(question.get_absolute_url())


@require_POST
@login_required
def unwatch_question(request, question_id):
    """Stop watching a question."""
    question = get_object_or_404(Question, pk=question_id)
    QuestionReplyEvent.stop_notifying(request.user, question)
    QuestionSolvedEvent.stop_notifying(request.user, question)
    return HttpResponseRedirect(question.get_absolute_url())


@require_GET
def unsubscribe_watch(request, watch_id, secret):
    """Stop watching a question, for anonymous users."""
    watch = get_object_or_404(Watch, pk=watch_id)
    question = watch.content_object
    success = False
    if watch.secret == secret and isinstance(question, Question):
        user_or_email = watch.user or watch.email
        QuestionReplyEvent.stop_notifying(user_or_email, question)
        QuestionSolvedEvent.stop_notifying(user_or_email, question)
        success = True

    return jingo.render(request, 'questions/unsubscribe_watch.html',
                        {'question': question, 'success': success})


@require_GET
def activate_watch(request, watch_id, secret):
    """Activate watching a question."""
    watch = get_object_or_404(Watch, pk=watch_id)
    question = watch.content_object
    if watch.secret == secret and isinstance(question, Question):
        watch.activate().save()
        statsd.incr('questions.watches.activate')

    return jingo.render(request, 'questions/activate_watch.html',
                        {'question': question,
                         'unsubscribe_url': reverse('questions.unsubscribe',
                                                    args=[watch_id, secret]),
                         'is_active': watch.is_active})


@login_required
@require_POST
def answer_preview_async(request):
    """Create an HTML fragment preview of the posted wiki syntax."""
    statsd.incr('questions.preview')
    answer = Answer(creator=request.user,
                    content=request.POST.get('content', ''))
    return jingo.render(request, 'questions/includes/answer_preview.html',
                        {'answer_preview': answer})


@mobile_template('questions/{mobile/}marketplace.html')
def marketplace(request, template=None):
    """AAQ landing page for Marketplace."""
    return jingo.render(request, template, {
        'categories': MARKETPLACE_CATEGORIES})


@anonymous_csrf
@mobile_template('questions/{mobile/}marketplace_category.html')
def marketplace_category(request, category_slug, template=None):
    """AAQ category page. Handles form post that submits ticket."""
    try:
        category_name = MARKETPLACE_CATEGORIES[category_slug]
    except KeyError:
        raise Http404

    error_message = None

    if request.method == 'GET':
        form = MarketplaceAaqForm(request.user)
    else:
        form = MarketplaceAaqForm(request.user, request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            category = form.cleaned_data['category']

            if request.user.is_authenticated():
                email = request.user.email
            else:
                email = form.cleaned_data['email']

            # Submit ticket
            try:
                submit_ticket(email, category, subject, body)
            except ZendeskError:
                error_message = _('There was an error submitting the ticket, '
                                  'please try again later.')

            if not error_message:
                return HttpResponseRedirect(
                    reverse('questions.marketplace_aaq_success'))

    return jingo.render(request, template, {
        'category': category_name,
        'category_slug': category_slug,
        'categories': MARKETPLACE_CATEGORIES,
        'form': form,
        'error_message': error_message})


@mobile_template('questions/{mobile/}marketplace_success.html')
def marketplace_success(request, template=None):
    """Confirmation of ticket submitted successfully."""
    return jingo.render(request, template)


def _search_suggestions_es(request, query, locale, category_tags):
    """See _search_suggestions

    """
    # TODO: this can be reworked to pull data from ES rather than
    # hit the db.
    engine = 'elastic'
    question_s = Question.search()
    wiki_s = Document.search()

    # Max number of search results per type.
    WIKI_RESULTS = QUESTIONS_RESULTS = 3
    default_categories = settings.SEARCH_DEFAULT_CATEGORIES

    # Apply category filters
    if category_tags:
        question_s = question_s.filter(question_tag__in=category_tags)
        wiki_s = wiki_s.filter(document_tag__in=category_tags)

    try:
        raw_results = (
            wiki_s.filter(document_locale=locale,
                          document_category__in=default_categories)
                  .query(query)
                  .values_dict('id')[:WIKI_RESULTS])

        results = []
        for r in raw_results:
            try:
                doc = (Document.objects.select_related('current_revision')
                                       .get(pk=r['id']))
                results.append({
                    'search_summary': clean_excerpt(
                            doc.current_revision.summary),
                    'url': doc.get_absolute_url(),
                    'title': doc.title,
                    'type': 'document',
                    'object': doc,
                })
            except Document.DoesNotExist:
                pass

        # Note: Questions app is en-US only.
        raw_results = (question_s.query(query)
                                 .values_dict('id')[:QUESTIONS_RESULTS])

        for r in raw_results:
            try:
                q = Question.objects.get(pk=r['id'])
                results.append({
                    'search_summary': clean_excerpt(q.content[0:500]),
                    'url': q.get_absolute_url(),
                    'title': q.title,
                    'type': 'question',
                    'object': q,
                    'is_solved': q.is_solved,
                    'num_answers': q.num_answers,
                    'num_votes': q.num_votes,
                    'num_votes_past_week': q.num_votes_past_week
                })
            except Question.DoesNotExist:
                pass

    except (SearchError, ESTimeoutError, ESMaxRetryError, ESException), exc:
        if isinstance(exc, SearchError):
            statsd.incr('questions.suggestions.%s.searcherror' % engine)
        elif isinstance(exc, ESTimeoutError):
            statsd.incr('questions.suggestions.%s.timeouterror' % engine)
        elif isinstance(exc, ESMaxRetryError):
            statsd.incr('questions.suggestions.%s.maxretryerror' % engine)
        elif isinstance(exc, ESException):
            statsd.incr('questions.suggestions.%s.elasticsearchexception' %
                        engine)

        return []

    return results


def _search_suggestions_sphinx(request, query, locale, category_tags):
    """Return an iterable of the most relevant wiki pages and questions.

    query -- full text to search on
    locale -- locale to limit to

    Items are dicts of:
        {
            'type':
            'search_summary':
            'title':
            'url':
            'object':
        }

    Returns up to 3 wiki pages, then up to 3 questions.

    """
    if waffle.flag_is_active(request, 'elasticsearch'):
        engine = 'elastic'
        question_s = Question.search()
        wiki_s = Document.search()
    else:
        engine = 'sphinx'
        question_s = question_searcher(request)
        wiki_s = wiki_searcher(request)

    # Max number of search results per type.
    WIKI_RESULTS = QUESTIONS_RESULTS = 3

    # Apply category filters
    if category_tags:
        question_s = question_s.filter(tag__in=category_tags)
        wiki_s = wiki_s.filter(tag__in=category_tags)

    try:
        raw_results = (
            wiki_s.filter(locale=locale,
                          category__in=settings.SEARCH_DEFAULT_CATEGORIES)
                  .query(query)
                  .values_dict('id')[:WIKI_RESULTS])

        results = []
        for r in raw_results:
            try:
                doc = (Document.objects.select_related('current_revision')
                                       .get(pk=r['id']))
                results.append({
                    'search_summary': clean_excerpt(
                            doc.current_revision.summary),
                    'url': doc.get_absolute_url(),
                    'title': doc.title,
                    'type': 'document',
                    'object': doc,
                })
            except Document.DoesNotExist:
                pass

        # Note: Questions app is en-US only.
        raw_results = (question_s.query(query)
                                 .values_dict('id')[:QUESTIONS_RESULTS])

        for r in raw_results:
            try:
                q = Question.objects.get(pk=r['id'])
                results.append({
                    'search_summary': clean_excerpt(q.content[0:500]),
                    'url': q.get_absolute_url(),
                    'title': q.title,
                    'type': 'question',
                    'is_solved': q.is_solved,
                    'num_answers': q.num_answers,
                    'num_votes': q.num_votes,
                    'num_votes_past_week': q.num_votes_past_week
                })
            except Question.DoesNotExist:
                pass

    except (SearchError, ESTimeoutError, ESMaxRetryError, ESException), exc:
        if isinstance(exc, SearchError):
            statsd.incr('questions.suggestions.%s.searcherror' % engine)
        elif isinstance(exc, ESTimeoutError):
            statsd.incr('questions.suggestions.%s.timeouterror' % engine)
        elif isinstance(exc, ESMaxRetryError):
            statsd.incr('questions.suggestions.%s.maxretryerror' % engine)
        elif isinstance(exc, ESException):
            statsd.incr('questions.suggestions.%s.elasticsearchexception' %
                        engine)

        return []

    return results


def _search_suggestions(request, query, locale, category_tags):
    """Return an iterable of the most relevant wiki pages and questions.

    query -- full text to search on
    locale -- locale to limit to

    Items are dicts of:
        {
            'type':
            'search_summary':
            'title':
            'url':
            'object':
        }

    Returns up to 3 wiki pages, then up to 3 questions.

    """
    if waffle.flag_is_active(request, 'elasticsearch'):
        return _search_suggestions_es(request, query, locale, category_tags)
    else:
        return _search_suggestions_sphinx(request, query, locale,
                                          category_tags)


def _answers_data(request, question_id, form=None, watch_form=None,
                  answer_preview=None):
    """Return a map of the minimal info necessary to draw an answers page."""
    question = get_object_or_404(Question, pk=question_id)
    answers_ = paginate(request, question.answers.all(),
                        per_page=constants.ANSWERS_PER_PAGE)
    feed_urls = ((reverse('questions.answers.feed',
                          kwargs={'question_id': question_id}),
                  AnswersFeed().title(question)),)
    frequencies = dict(FREQUENCY_CHOICES)

    is_watching_question = (
        request.user.is_authenticated() and (
        QuestionReplyEvent.is_notifying(request.user, question) or
        QuestionSolvedEvent.is_notifying(request.user, question)))
    return {'question': question,
            'answers': answers_,
            'form': form or AnswerForm(),
            'answer_preview': answer_preview,
            'watch_form': watch_form or _init_watch_form(request, 'reply'),
            'feeds': feed_urls,
            'frequencies': frequencies,
            'is_watching_question': is_watching_question,
            'can_tag': request.user.has_perm('questions.tag_question'),
            'can_create_tags': request.user.has_perm('taggit.add_tag')}


def _add_tag(request, question_id):
    """Add a named tag to a question, creating it first if appropriate.

    Tag name (case-insensitive) must be in request.POST['tag-name'].

    If there is no such tag and the user is not allowed to make new tags, raise
    Tag.DoesNotExist. If no tag name is provided, return None. Otherwise,
    return the canonicalized tag name.

    """
    tag_name = request.POST.get('tag-name', '').strip()
    if tag_name:
        question = get_object_or_404(Question, pk=question_id)
        try:
            canonical_name = add_existing_tag(tag_name, question.tags)
        except Tag.DoesNotExist:
            if request.user.has_perm('taggit.add_tag'):
                question.tags.add(tag_name)  # implicitly creates if needed
                return question, tag_name
            raise
        return question, canonical_name

    return None, None


def _get_top_contributors():
    """Retrieves the top contributors from cache, if available.

    These are the users with the most solutions in the last week.
    """
    return cache.get(settings.TOP_CONTRIBUTORS_CACHE_KEY)


# Initialize a WatchQuestionForm
def _init_watch_form(request, event_type='solution'):
    initial = {'event_type': event_type}
    return WatchQuestionForm(request.user, initial=initial)
