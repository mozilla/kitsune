import json
import logging
import random
import time
from datetime import date, datetime, timedelta

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
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (require_POST, require_GET,
                                          require_http_methods)

import jingo
import waffle
from ordereddict import OrderedDict
from mobility.decorators import mobile_template
from ratelimit.decorators import ratelimit
from ratelimit.helpers import is_ratelimited
from session_csrf import anonymous_csrf
from statsd import statsd
from taggit.models import Tag
from tidings.events import ActivationRequestFailed
from tidings.models import Watch
from tower import ugettext as _, ugettext_lazy as _lazy

from kitsune.access.decorators import permission_required, login_required
from kitsune.karma.manager import KarmaManager
from kitsune.products.models import Product, Topic
from kitsune.questions import config
from kitsune.questions.events import QuestionReplyEvent, QuestionSolvedEvent
from kitsune.questions.feeds import (
    QuestionsFeed, AnswersFeed, TaggedQuestionsFeed)
from kitsune.questions.forms import (
    NewQuestionForm, EditQuestionForm, AnswerForm, WatchQuestionForm,
    FREQUENCY_CHOICES, MarketplaceAaqForm, MarketplaceRefundForm,
    MarketplaceDeveloperRequestForm, StatsForm)
from kitsune.questions.karma_actions import (
    SolutionAction, AnswerMarkedHelpfulAction, AnswerMarkedNotHelpfulAction)
from kitsune.questions.marketplace import (
    MARKETPLACE_CATEGORIES, ZendeskError)
from kitsune.questions.models import (
    Question, Answer, QuestionVote, AnswerVote, QuestionMappingType)
from kitsune.questions.signals import tag_added
from kitsune.search.es_utils import (ES_EXCEPTIONS, Sphilastic, F,
                                     es_query_with_analyzer)
from kitsune.search.utils import locale_or_default, clean_excerpt
from kitsune.sumo.decorators import ssl_required
from kitsune.sumo.helpers import urlparams
from kitsune.sumo.urlresolvers import reverse, split_path
from kitsune.sumo.utils import (
    paginate, simple_paginate, build_paged_url, user_or_ip)
from kitsune.tags.utils import add_existing_tag
from kitsune.upload.models import ImageAttachment
from kitsune.upload.views import upload_imageattachment
from kitsune.users.forms import RegisterForm
from kitsune.users.models import Setting
from kitsune.users.utils import handle_login, handle_register
from kitsune.wiki.facets import documents_for, topics_for
from kitsune.wiki.models import Document, DocumentMappingType


log = logging.getLogger('k.questions')


UNAPPROVED_TAG = _lazy(u'That tag does not exist.')
NO_TAG = _lazy(u'Please provide a tag.')

FILTER_GROUPS = {
    'all': OrderedDict([
        ('recently-unanswered', _lazy('Recently unanswered')),
    ]),
    'needs-attention': OrderedDict([
        ('new', _lazy('New')),
        ('unhelpful-answers', _lazy("Answers didn't help")),
    ]),
    'responded': OrderedDict([
        ('needsinfo', _lazy('Needs info')),
        ('solution-provided', _lazy('Solution provided')),
    ]),
    'done': OrderedDict([
        ('solved', _lazy('Solved')),
        ('locked', _lazy('Locked')),
    ]),
}


@mobile_template('questions/{mobile/}questions.html')
def questions(request, template):
    """View the questions."""

    filter_ = request.GET.get('filter')
    owner = request.GET.get(
        'owner', request.session.get('questions_owner', 'all'))
    show = request.GET.get('show', 'needs-attention')
    escalated = int(request.GET.get(
        'escalated', request.session.get('questions_escalated', False)))
    offtopic = int(request.GET.get(
        'offtopic', request.session.get('questions_offtopic', False)))
    tagged = request.GET.get('tagged')
    tags = None
    product_slug = request.GET.get('product')
    topic_slug = request.GET.get('topic')

    if product_slug:
        product = get_object_or_404(Product, slug=product_slug)
    else:
        product = None

    if topic_slug and product:
        try:
            topic = Topic.objects.get(slug=topic_slug, product=product)
        except Topic.DoesNotExist:
            topic = None
    else:
        topic = None

    question_qs = Question.objects

    if show not in FILTER_GROUPS:
        show = None
    else:
        if filter_ not in FILTER_GROUPS[show]:
            filter_ = None

        if filter_ == 'new':
            question_qs = question_qs.new()
        elif filter_ == 'unhelpful-answers':
            question_qs = question_qs.unhelpful_answers()
        elif filter_ == 'needsinfo':
            question_qs = question_qs.needs_info()
        elif filter_ == 'solution-provided':
            question_qs = question_qs.solution_provided()
        elif filter_ == 'solved':
            question_qs = question_qs.solved()
        elif filter_ == 'locked':
            question_qs = question_qs.locked()
        elif filter_ == 'recently-unanswered':
            question_qs = question_qs.recently_unanswered()
        else:
            if show == 'needs-attention':
                question_qs = question_qs.needs_attention()
            if show == 'responded':
                question_qs = question_qs.responded()
            if show == 'done':
                question_qs = question_qs.done()

    question_qs = question_qs.select_related(
        'creator', 'last_answer', 'last_answer__creator')

    question_qs = question_qs.filter(creator__is_active=1)

    if owner == 'mine' and request.user.is_authenticated():
        criteria = Q(answers__creator=request.user) | Q(creator=request.user)
        question_qs = question_qs.filter(criteria).distinct()
    else:
        owner = None

    if escalated:
        question_qs = question_qs.filter(
            tags__slug__in=[config.ESCALATE_TAG_NAME])

    if offtopic:
        question_qs = question_qs.filter(
            tags__slug__in=[config.OFFTOPIC_TAG_NAME])

    feed_urls = ((urlparams(reverse('questions.feed'),
                            product=product_slug, topic=topic_slug),
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

    # Filter by product.
    if product:
        # This filter will match if any of the products on a question have the
        # correct id.
        question_qs = question_qs.filter(products__id__exact=product.id)

    # Filter by topic.
    if topic:
        # This filter will match if any of the topics on a question have the
        # correct id.
        question_qs = question_qs.filter(topics__id__exact=topic.id)

    # Filter by locale for AAQ locales, and by locale + default for others.
    if request.LANGUAGE_CODE in settings.AAQ_LANGUAGES:
        locale_query = Q(locale=request.LANGUAGE_CODE)
    else:
        locale_query = Q(locale=request.LANGUAGE_CODE)
        locale_query |= Q(locale=settings.WIKI_DEFAULT_LANGUAGE)

    question_qs = question_qs.filter(locale_query)

    # Set the order.
    question_qs = question_qs.order_by('-updated')

    try:
        with statsd.timer('questions.view.paginate.%s' % filter_):
            questions_page = simple_paginate(
                request, question_qs, per_page=config.QUESTIONS_PER_PAGE)
    except (PageNotAnInteger, EmptyPage):
        # If we aren't on page 1, redirect there.
        # TODO: Is 404 more appropriate?
        if request.GET.get('page', '1') != '1':
            url = build_paged_url(request)
            return HttpResponseRedirect(urlparams(url, page=1))

    # Recent answered stats
    recent_asked_count = Question.recent_asked_count(locale_query)
    recent_unanswered_count = Question.recent_unanswered_count(locale_query)
    if recent_asked_count:
        recent_answered_percent = int(
            (float(recent_asked_count - recent_unanswered_count) /
            recent_asked_count) * 100)
    else:
        recent_answered_percent = 0

    # List of products to fill the selector.
    product_list = Product.objects.filter(visible=True)

    # List of topics to fill the selector.
    if product:
        topic_list = Topic.objects.filter(visible=True, product=product)[:10]
    else:
        topic_list = []

    # Store current filters in the session
    if request.user.is_authenticated():
        request.session['questions_owner'] = owner
        request.session['questions_escalated'] = escalated
        request.session['questions_offtopic'] = offtopic

    data = {'questions': questions_page,
            'feeds': feed_urls,
            'filter': filter_,
            'owner': owner,
            'show': show,
            'filters': FILTER_GROUPS[show],
            'escalated': escalated,
            'offtopic': offtopic,
            'tags': tags,
            'tagged': tagged,
            'recent_asked_count': recent_asked_count,
            'recent_unanswered_count': recent_unanswered_count,
            'recent_answered_percent': recent_answered_percent,
            'product_list': product_list,
            'product': product,
            'topic_list': topic_list,
            'topic': topic}

    if (waffle.flag_is_active(request, 'karma') and
        waffle.switch_is_active('karma')):
        kmgr = KarmaManager()
        data.update(karma_top=kmgr.top_users('3m', count=20))
        if request.user.is_authenticated():
            ranking = kmgr.ranking('3m', request.user)
            if ranking <= config.HIGHEST_RANKING:
                data.update(karma_ranking=ranking)
    else:
        data.update(top_contributors=_get_top_contributors())

    with statsd.timer('questions.view.render'):
        return render(request, template, data)


def parse_troubleshooting(troubleshooting_json):
    """Normalizes the troubleshooting data from `question`.

    Returns a normalized version, or `None` if something was wrong.
    This does not try very hard to fix bad data.
    """
    if not troubleshooting_json:
        return None
    try:
        parsed = json.loads(troubleshooting_json)
    except ValueError:
        return None

    # This is a spec of what is expected to be in the parsed
    # troubleshooting data. The format here is a list of tuples. The
    # first item in the tuple is a list of keys to access to get to the
    # item in question. The second item in the tuple is the type the
    # referenced item should be. For example, this line
    #
    #   (('application', 'name'), basestring),
    #
    # means that parse['application']['name'] must be a basestring.
    #
    # An empty path means the parsed json.
    spec = (
        ((), dict),
        (('accessibility', ), dict),
        (('accessibility', 'isActive'), bool),
        (('application', ), dict),
        (('application', 'name'), basestring),
        (('application', 'supportURL'), basestring),
        (('application', 'userAgent'), basestring),
        (('application', 'version'), basestring),
        (('extensions', ), list),
        (('graphics', ), dict),
        (('javaScript', ), dict),
        (('modifiedPreferences', ), dict),
        (('userJS', ), dict),
        (('userJS', 'exists'), bool),
    )

    for path, type_ in spec:
        item = parsed
        for piece in path:
            item = item.get(piece)
            if item is None:
                return None

        if not isinstance(item, type_):
            return None

    # The data has been inspected, and should be in the right format.
    # Now remove all the printing preferences, because they are noisy.
    # TODO: If the UI for this gets better, we can include these prefs
    # and just make them collapsible.

    parsed['modifiedPreferences'] = dict(
        (key, val) for (key, val) in parsed['modifiedPreferences'].items()
        if not key.startswith('print'))

    return parsed


@mobile_template('questions/{mobile/}answers.html')
@anonymous_csrf  # Need this so the anon csrf gets set for watch forms.
def answers(request, template, question_id, form=None, watch_form=None,
            answer_preview=None, **extra_kwargs):
    """View the answers to a question."""
    ans_ = _answers_data(request, question_id, form, watch_form,
                         answer_preview)
    question = ans_['question']

    # Try to parse troubleshooting data as JSON.
    troubleshooting_json = question.metadata.get('troubleshooting')
    question.metadata['troubleshooting_parsed'] = (
                        parse_troubleshooting(troubleshooting_json))

    if request.user.is_authenticated():
        ans_['images'] = question.images.filter(creator=request.user)

    extra_kwargs.update(ans_)

    product = Product.uncached.filter(question=question)
    topic = Topic.uncached.filter(question=question)

    products = Product.objects.filter(visible=True)
    topics = topics_for(products=[question.products.all()])

    extra_kwargs.update({'all_products': products, 'all_topics': topics,
                         'product': product, 'topic': topic})

    # Add noindex to questions without answers that are > 30 days old.
    if not request.MOBILE:
        no_answers = ans_['answers'].paginator.count == 0
        if (no_answers and
            question.created < datetime.now() - timedelta(days=30)):
            extra_kwargs.update(robots_noindex=True)

    return render(request, template, extra_kwargs)


@require_POST
@permission_required('questions.change_question')
def edit_details(request, question_id):
    try:
        product = Product.objects.get(id=request.POST.get('product'))
        topic = Topic.objects.get(id=request.POST.get('topic'),
                                  product=product)
    except (Product.DoesNotExist, Topic.DoesNotExist):
        return HttpResponseBadRequest()

    question = get_object_or_404(Question, pk=question_id)
    question.products = [product]
    question.topics = [topic]
    question.save()

    return redirect(reverse('questions.answers',
                            kwargs={'question_id': question_id}))


@ssl_required
@mobile_template('questions/{mobile/}new_question.html')
@anonymous_csrf  # This view renders a login form
def aaq(request, product_key=None, category_key=None, showform=False,
        template=None, step=0):
    """Ask a new question."""

    if request.LANGUAGE_CODE not in settings.AAQ_LANGUAGES:
        locale, path = split_path(request.path)
        path = '/' + settings.WIKI_DEFAULT_LANGUAGE + '/' + path

        old_lang = settings.LANGUAGES[request.LANGUAGE_CODE.lower()]
        new_lang = settings.LANGUAGES[settings.WIKI_DEFAULT_LANGUAGE.lower()]
        msg = (_(u"The questions forum isn't available in {old_lang}, we "
                 u"have redirected you to the {new_lang} questions forum.")
               .format(old_lang=old_lang, new_lang=new_lang))
        messages.add_message(request, messages.WARNING, msg)

        return HttpResponseRedirect(path)

    if product_key is None:
        product_key = request.GET.get('product')
        if request.MOBILE and product_key is None:
            # Firefox OS is weird. The best way we can detect it is to
            # look for a mobile Firefox that is not Android.
            ua = request.META.get('HTTP_USER_AGENT', '').lower()
            if 'firefox' in ua and 'android' not in ua:
                product_key = 'firefox-os'
            else:
                product_key = 'mobile'

    product = config.products.get(product_key)
    if product_key and not product:
        raise Http404

    if category_key is None:
        category_key = request.GET.get('category')

    if product and category_key:
        product_obj = Product.objects.filter(slug__in=product.get('products'))
        category = product['categories'].get(category_key)
        if not category:
            # If we get an invalid category, redirect to previous step.
            return HttpResponseRedirect(
                reverse('questions.aaq_step2', args=[product_key]))
        deadend = category.get('deadend', False)
        topic = category.get('topic')
        if topic:
            html = None
            articles, fallback = documents_for(
                locale=request.LANGUAGE_CODE,
                products=product_obj,
                topics=[Topic.objects.get(slug=topic, product=product_obj)])
        else:
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
            results = _search_suggestions(
                request,
                search,
                locale_or_default(request.LANGUAGE_CODE),
                product.get('products'))
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
                return render(request, login_t, {
                    'product': product, 'category': category,
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

        return render(request, template, {
            'form': form,
            'results': results,
            'tried_search': tried_search,
            'products': config.products,
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

            if login_form.is_valid():
                statsd.incr('questions.user.login.success')
            else:
                statsd.incr('questions.user.login.fail')

        elif request.POST.get('register'):
            login_form = AuthenticationForm()
            register_form = handle_register(
                request=request,
                text_template='questions/email/confirm_question.ltxt',
                html_template='questions/email/confirm_question.html',
                subject=_('Please confirm your Firefox Help question'),
                email_data=request.GET.get('search'))

            if register_form.is_valid():  # Now try to log in.
                user = auth.authenticate(username=request.POST.get('username'),
                                         password=request.POST.get('password'))
                auth.login(request, user)
                statsd.incr('questions.user.register')
        else:
            # L10n: This shouldn't happen unless people tamper with POST data.
            message = _lazy('Request type not recognized.')
            return render(request, 'handlers/400.html', {
                'message': message}, status=400)
        if request.user.is_authenticated():
            # Redirect to GET the current URL replacing the step parameter.
            # This is also required for the csrf middleware to set the auth'd
            # tokens appropriately.
            url = urlparams(request.get_full_path(), step='aaq-question')
            return HttpResponseRedirect(url)
        else:
            return render(request, login_t, {
                'product': product, 'category': category,
                'title': request.POST.get('title'),
                'register_form': register_form,
                'login_form': login_form})

    form = NewQuestionForm(product=product, category=category,
                           data=request.POST)

    if form.is_valid() and not is_ratelimited(request, increment=True,
                                              rate='5/d', ip=False,
                                              keys=user_or_ip('aaq-day')):
        question = Question(creator=request.user,
                            title=form.cleaned_data['title'],
                            content=form.cleaned_data['content'],
                            locale=request.LANGUAGE_CODE)
        question.save()
        # User successfully submitted a new question
        statsd.incr('questions.new')
        question.add_metadata(**form.cleaned_metadata)
        if product:
            # TODO: This add_metadata call should be removed once we are
            # fully IA-driven (sync isn't special case anymore).
            question.add_metadata(product=product['key'])

            if product.get('products'):
                for p in Product.objects.filter(slug__in=product['products']):
                    question.products.add(p)

            if category:
                # TODO: This add_metadata call should be removed once we are
                # fully IA-driven (sync isn't special case anymore).
                question.add_metadata(category=category['key'])

                t = category.get('topic')
                if t:
                    question.topics.add(Topic.objects.get(slug=t,
                                                          product=product_obj))

        # The first time a question is saved, automatically apply some tags:
        question.auto_tag()

        # Submitting the question counts as a vote
        question_vote(request, question.id)

        if request.user.is_active:
            messages.add_message(request, messages.SUCCESS,
                _('Done! Your question is now posted on the Mozilla community '
                  'support forum.'))
            url = reverse('questions.answers',
                          kwargs={'question_id': question.id})
            return HttpResponseRedirect(url)

        return HttpResponseRedirect(reverse('questions.aaq_confirm'))

    if getattr(request, 'limited', False):
        raise PermissionDenied

    statsd.incr('questions.aaq.details-form-error')
    return render(request, template, {
        'form': form,
        'products': config.products,
        'current_product': product,
        'current_category': category,
        'current_articles': articles})


@ssl_required
def aaq_step2(request, product_key):
    """Step 2: The product is selected."""
    return aaq(request, product_key=product_key, step=1)


@ssl_required
def aaq_step3(request, product_key, category_key):
    """Step 3: The product and category is selected."""
    return aaq(request, product_key=product_key, category_key=category_key,
               step=1)


@ssl_required
def aaq_step4(request, product_key, category_key):
    """Step 4: Search query entered."""
    return aaq(request, product_key=product_key, category_key=category_key,
               step=1)


@ssl_required
def aaq_step5(request, product_key, category_key):
    """Step 5: Show full question form."""
    return aaq(request, product_key=product_key, category_key=category_key,
               showform=True, step=3)


def aaq_confirm(request):
    """AAQ confirm email step for new users."""
    if request.user.is_authenticated():
        email = request.user.email
        auth.logout(request)
        statsd.incr('questions.user.logout')
    else:
        email = None

    confirm_t = ('questions/mobile/confirm_email.html' if request.MOBILE
                     else 'questions/confirm_email.html')
    return render(request, confirm_t, {'email': email})


@require_http_methods(['GET', 'POST'])
@login_required
def edit_question(request, question_id):
    """Edit a question."""
    question = get_object_or_404(Question, pk=question_id)
    user = request.user

    if not question.allows_edit(user):
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

    return render(request, 'questions/edit_question.html', {
        'question': question,
        'form': form,
        'current_product': question.product,
        'current_category': question.category})


def _skip_answer_ratelimit(request):
    """Exclude image uploading and deleting from the reply rate limiting.

    Also exclude users with the questions.bypass_ratelimit permission.
    """
    return ('delete_images' in request.POST or
            'upload_image' in request.POST or
            request.user.has_perm('questions.bypass_answer_ratelimit'))


@require_POST
@login_required
@ratelimit(keys=user_or_ip('answer-min'), skip_if=_skip_answer_ratelimit,
           ip=False, rate='4/m')
@ratelimit(keys=user_or_ip('answer-day'), skip_if=_skip_answer_ratelimit,
           ip=False, rate='100/d')
def reply(request, question_id):
    """Post a new answer to a question."""
    question = get_object_or_404(Question, pk=question_id)
    answer_preview = None

    if not question.allows_new_answer(request.user):
        raise PermissionDenied

    form = AnswerForm(request.POST)

    # NOJS: delete images
    if 'delete_images' in request.POST:
        for image_id in request.POST.getlist('delete_image'):
            ImageAttachment.objects.get(pk=image_id).delete()

        return answers(request, question_id=question_id, form=form)

    # NOJS: upload image
    if 'upload_image' in request.POST:
        upload_imageattachment(request, question)
        return answers(request, question_id=question_id, form=form)

    if form.is_valid() and not request.limited:
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

    return answers(request, question_id=question_id, form=form,
                   answer_preview=answer_preview)


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

    if not question.allows_solve(request.user):
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

    if not question.allows_unsolve(request.user):
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
@ratelimit(keys=user_or_ip('question-vote'), ip=False, rate='10/d')
def question_vote(request, question_id):
    """I have this problem too."""
    question = get_object_or_404(Question, pk=question_id)

    if not question.editable:
        raise PermissionDenied

    if not question.has_voted(request):
        vote = QuestionVote(question=question)

        if request.user.is_authenticated():
            vote.creator = request.user
        else:
            vote.anonymous_id = request.anonymous.anonymous_id

        if not request.limited:
            vote.save()

            if 'referrer' in request.REQUEST:
                referrer = request.REQUEST.get('referrer')
                vote.add_metadata('referrer', referrer)

                if referrer == 'search' and 'query' in request.REQUEST:
                    vote.add_metadata('query', request.REQUEST.get('query'))

            ua = request.META.get('HTTP_USER_AGENT')
            if ua:
                vote.add_metadata('ua', ua[:1000])  # 1000 max_length
            statsd.incr('questions.votes.question')

        if request.is_ajax():
            tmpl = 'questions/includes/question_vote_thanks.html'
            form = _init_watch_form(request)
            html = jingo.render_to_string(request, tmpl, {'question': question,
                                                          'watch_form': form})

            return HttpResponse(json.dumps({
                'html': html,
                'ignored': request.limited
            }))

    return HttpResponseRedirect(question.get_absolute_url())


@csrf_exempt
@ratelimit(keys=user_or_ip('answer-vote'), ip=False, rate='10/d')
def answer_vote(request, question_id, answer_id):
    """Vote for Helpful/Not Helpful answers"""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)

    if not answer.question.editable:
        raise PermissionDenied

    if request.limited:
        if request.is_ajax():
            return HttpResponse(json.dumps({"ignored": True}))
        else:
            return HttpResponseRedirect(answer.get_absolute_url())

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

        if 'referrer' in request.REQUEST:
            referrer = request.REQUEST.get('referrer')
            vote.add_metadata('referrer', referrer)

            if referrer == 'search' and 'query' in request.REQUEST:
                vote.add_metadata('query', request.REQUEST.get('query'))

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
        return render(request, 'questions/answers.html', template_data)

    if canonical_name:  # success
        question.clear_cached_tags()
        return HttpResponseRedirect(
            reverse('questions.answers', args=[question_id]))

    # No tag provided
    template_data = _answers_data(request, question_id)
    template_data['tag_adding_error'] = NO_TAG
    return render(request, 'questions/answers.html', template_data)


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
def delete_question(request, question_id):
    """Delete a question"""
    question = get_object_or_404(Question, pk=question_id)

    if not question.allows_delete(request.user):
        raise PermissionDenied

    if request.method == 'GET':
        # Render the confirmation page
        return render(request, 'questions/confirm_question_delete.html', {
            'question': question})

    # Handle confirm delete form POST
    log.warning('User %s is deleting question with id=%s' %
                (request.user, question.id))
    question.delete()

    return HttpResponseRedirect(reverse('questions.questions'))


@login_required
def delete_answer(request, question_id, answer_id):
    """Delete an answer"""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)

    if not answer.allows_delete(request.user):
        raise PermissionDenied

    if request.method == 'GET':
        # Render the confirmation page
        return render(request, 'questions/confirm_answer_delete.html', {
            'answer': answer})

    # Handle confirm delete form POST
    log.warning('User %s is deleting answer with id=%s' %
                (request.user, answer.id))
    answer.delete()

    return HttpResponseRedirect(reverse('questions.answers',
                                args=[question_id]))


@require_POST
@login_required
def lock_question(request, question_id):
    """Lock or unlock a question"""
    question = get_object_or_404(Question, pk=question_id)

    if not question.allows_lock(request.user):
        raise PermissionDenied

    question.is_locked = not question.is_locked
    log.info("User %s set is_locked=%s on question with id=%s " %
             (request.user, question.is_locked, question.id))
    question.save()

    return HttpResponseRedirect(question.get_absolute_url())


@require_POST
@login_required
def archive_question(request, question_id):
    """Archive or unarchive a question"""
    question = get_object_or_404(Question, pk=question_id)

    if not question.allows_archive(request.user):
        raise PermissionDenied

    question.is_archived = not question.is_archived
    log.info("User %s set is_archived=%s on question with id=%s " %
             (request.user, question.is_archived, question.id))
    question.save()

    return HttpResponseRedirect(question.get_absolute_url())


@login_required
def edit_answer(request, question_id, answer_id):
    """Edit an answer."""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)
    answer_preview = None

    if not answer.allows_edit(request.user):
        raise PermissionDenied

    # NOJS: upload images, if any
    upload_imageattachment(request, answer)

    if request.method == 'GET':
        form = AnswerForm({'content': answer.content})
        return render(request, 'questions/edit_answer.html', {
            'form': form, 'answer': answer})

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

    return render(request, 'questions/edit_answer.html', {
        'form': form, 'answer': answer,
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

    return render(request, 'questions/unsubscribe_watch.html', {
        'question': question, 'success': success})


@require_GET
def activate_watch(request, watch_id, secret):
    """Activate watching a question."""
    watch = get_object_or_404(Watch, pk=watch_id)
    question = watch.content_object
    if watch.secret == secret and isinstance(question, Question):
        watch.activate().save()
        statsd.incr('questions.watches.activate')

    return render(request, 'questions/activate_watch.html', {
        'question': question,
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
    template = 'questions/includes/answer_preview.html'

    return render(request, template, {'answer_preview': answer})


@mobile_template('questions/{mobile/}marketplace.html')
def marketplace(request, template=None):
    """AAQ landing page for Marketplace."""
    return render(request, template, {
        'categories': MARKETPLACE_CATEGORIES})


ZENDESK_ERROR_MESSAGE = _lazy(
    u'There was an error submitting the ticket. '
    u'Please try again later.')


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
            # Submit ticket
            try:
                form.submit_ticket()

                return HttpResponseRedirect(
                    reverse('questions.marketplace_aaq_success'))

            except ZendeskError:
                error_message = ZENDESK_ERROR_MESSAGE

    return render(request, template, {
        'category': category_name,
        'category_slug': category_slug,
        'categories': MARKETPLACE_CATEGORIES,
        'form': form,
        'error_message': error_message})


@anonymous_csrf
@mobile_template('questions/{mobile/}marketplace_refund.html')
def marketplace_refund(request, template):
    """Form page that handles refund requests for Marketplace."""
    error_message = None

    if request.method == 'GET':
        form = MarketplaceRefundForm(request.user)
    else:
        form = MarketplaceRefundForm(request.user, request.POST)
        if form.is_valid():
            # Submit ticket
            try:
                form.submit_ticket()

                return HttpResponseRedirect(
                    reverse('questions.marketplace_aaq_success'))

            except ZendeskError:
                error_message = ZENDESK_ERROR_MESSAGE

    return render(request, template, {
        'form': form,
        'error_message': error_message})


@anonymous_csrf
@mobile_template('questions/{mobile/}marketplace_developer_request.html')
def marketplace_developer_request(request, template):
    """Form page that handles developer requests for Marketplace."""
    error_message = None

    if request.method == 'GET':
        form = MarketplaceDeveloperRequestForm(request.user)
    else:
        form = MarketplaceDeveloperRequestForm(request.user, request.POST)
        if form.is_valid():
            # Submit ticket
            try:
                form.submit_ticket()

                return HttpResponseRedirect(
                    reverse('questions.marketplace_aaq_success'))

            except ZendeskError:
                error_message = ZENDESK_ERROR_MESSAGE

    return render(request, template, {
        'form': form,
        'error_message': error_message})


@mobile_template('questions/{mobile/}marketplace_success.html')
def marketplace_success(request, template=None):
    """Confirmation of ticket submitted successfully."""
    return render(request, template)


def stats_topic_data(bucket_days, start, end, locale=None):
    """Gets a zero filled histogram for each question topic.

    Uses elastic search.
    """
    search = Sphilastic(QuestionMappingType)

    bucket = 24 * 60 * 60 * bucket_days

    # datetime is a subclass of date.
    if isinstance(start, date):
        start = int(time.mktime(start.timetuple()))
    if isinstance(end, date):
        end = int(time.mktime(end.timetuple()))

    f = F(model='questions_question')
    f &= F(created__gt=start)
    f &= F(created__lt=end)

    if locale:
        f &= F(question_locale=locale)

    topics = Topic.objects.values('slug', 'title')
    facets = {}
    # TODO: If we change to using datetimes in ES, 'histogram' below
    # should change to 'date_histogram'.
    for topic in topics:
        filters = search._process_filters([f & F(topic=topic['slug'])])
        facets[topic['title']] = {
            'histogram': {'interval': bucket, 'field': 'created'},
            'facet_filter': filters
        }

    # Get some sweet histogram data.
    search = search.facet_raw(**facets).values_dict()
    try:
        histograms_data = search.facet_counts()
    except ES_EXCEPTIONS:
        return []

    # The data looks like this right now:
    # {
    #   'topic-1': [{'key': 1362774285, 'count': 100}, ...],
    #   'topic-2': [{'key': 1362774285, 'count': 100}, ...],
    # }

    # Massage the data to achieve 2 things:
    # - All points between the earliest and the latest values have data,
    #   at a resolution of 1 day.
    # - It is in a format usable by k.Graph.
    #   - ie: [{"created": 1362774285, 'topic-1': 10, 'topic-2': 20}, ...]

    for series in histograms_data.itervalues():
        if series:
            earliest_point = series[0]['key']
            break
    else:
        return []

    latest_point = earliest_point
    interim_data = {}

    for key, data in histograms_data.iteritems():
        if not data:
            continue
        for point in data:
            timestamp = point['key']
            value = point['count']

            earliest_point = min(earliest_point, timestamp)
            latest_point = max(latest_point, timestamp)

            datum = interim_data.get(timestamp, {'date': timestamp})
            datum[key] = value
            interim_data[timestamp] = datum

    # Interim data is now like
    # {
    #   1362774285: {'date': 1362774285, 'topic-1': 100, 'topic-2': 200},
    # }

    # Zero fill the interim data.
    timestamp = earliest_point
    while timestamp <= latest_point:
        datum = interim_data.get(timestamp, {'date': timestamp})
        for key in histograms_data.iterkeys():
            if key not in datum:
                datum[key] = 0
        timestamp += bucket

    # The keys are irrelevant, and the values are exactly what we want.
    return interim_data.values()


def metrics(request, locale_code=None):
    """The Support Forum metrics dashboard."""
    template = 'questions/metrics.html'

    form = StatsForm(request.GET)
    if form.is_valid():
        bucket_days = form.cleaned_data['bucket']
        start = form.cleaned_data['start']
        end = form.cleaned_data['end']
    else:
        bucket_days = 1
        start = date.today() - timedelta(days=30)
        end = date.today()

    data = {
        'graph': stats_topic_data(bucket_days, start, end, locale_code),
        'form': form,
        'current_locale': locale_code,
    }

    return render(request, template, data)


def _search_suggestions(request, text, locale, product_slugs):
    """Return an iterable of the most relevant wiki pages and questions.

    :arg text: full text to search on
    :arg locale: locale to limit to
    :arg product_slugs: list of product slugs to filter articles on
        (["desktop", "mobile", ...])

    Items are dicts of::

        {
            'type':
            'search_summary':
            'title':
            'url':
            'object':
        }

    :returns: up to 3 wiki pages, then up to 3 questions.

    """
    # TODO: this can be reworked to pull data from ES rather than
    # hit the db.
    question_s = QuestionMappingType.search()
    wiki_s = DocumentMappingType.search()

    # Max number of search results per type.
    WIKI_RESULTS = QUESTIONS_RESULTS = 3
    default_categories = settings.SEARCH_DEFAULT_CATEGORIES

    # Apply product filters
    if product_slugs:
        wiki_s = wiki_s.filter(product__in=product_slugs)
        question_s = question_s.filter(product__in=product_slugs)

    results = []
    try:
        # Search for relevant KB documents.
        query = dict(('%s__text' % field, text)
                      for field in DocumentMappingType.get_query_fields())
        query.update(dict(('%s__text_phrase' % field, text)
                      for field in DocumentMappingType.get_query_fields()))
        query = es_query_with_analyzer(query, locale)
        filter = F()
        filter |= F(document_locale=locale)
        filter |= F(document_locale=settings.WIKI_DEFAULT_LANGUAGE)
        filter &= F(document_category__in=default_categories)
        filter &= F(document_is_archived=False)

        raw_results = (
            wiki_s.filter(filter)
                  .query(or_=query)
                  .values_dict('id')[:WIKI_RESULTS])
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

        # Search for relevant questions.
        query = dict(('%s__text' % field, text)
                      for field in QuestionMappingType.get_query_fields())
        query.update(dict(('%s__text_phrase' % field, text)
                      for field in QuestionMappingType.get_query_fields()))

        max_age = int(time.time()) - settings.SEARCH_DEFAULT_MAX_QUESTION_AGE
        # Filter questions by language. Questions should be either in English
        # or in the locale's language. This is because we have some questions
        # marked English that are really in other languages. The assumption
        # being that if a native speakers submits a query in given language,
        # the items that are written in that language will automatically match
        # better, so questions incorrectly marked as english can be found too.
        question_filter = F(question_locale=locale)
        question_filter |= F(question_locale=settings.WIKI_DEFAULT_LANGUAGE)
        question_filter &= F(updated__gte=max_age)

        raw_results = (question_s
            .query(or_=query)
            .filter(question_filter)
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

    except ES_EXCEPTIONS as exc:
        statsd.incr('questions.suggestions.eserror')
        log.debug(exc)

    return results


def _answers_data(request, question_id, form=None, watch_form=None,
                  answer_preview=None):
    """Return a map of the minimal info necessary to draw an answers page."""
    question = get_object_or_404(Question, pk=question_id)
    answers_ = question.answers.all()
    if not request.MOBILE:
        answers_ = paginate(request, answers_,
                            per_page=config.ANSWERS_PER_PAGE)
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
                canonical_name = tag_name
            else:
                raise

        # Fire off the tag_added signal.
        tag_added.send(sender=Question, question_id=question.id,
                       tag_name=canonical_name)

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
