import json
import logging
import random
from collections import OrderedDict
from datetime import date, datetime, timedelta

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.db.models import Exists, F, OuterRef, Q
from django.db.models.functions import Now
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django_user_agents.utils import get_user_agent

from kitsune.access.decorators import login_required, permission_required
from kitsune.customercare.forms import ZendeskForm
from kitsune.flagit.models import FlaggedObject
from kitsune.flagit.views import get_hierarchical_topics
from kitsune.products import get_product_redirect_response
from kitsune.products.models import Product, Topic, TopicSlugHistory
from kitsune.questions import config
from kitsune.questions.events import QuestionReplyEvent, QuestionSolvedEvent
from kitsune.questions.feeds import AnswersFeed, QuestionsFeed, TaggedQuestionsFeed
from kitsune.questions.forms import (
    CRASH_ID_LABEL,
    FREQUENCY_CHOICES,
    FREQUENCY_LABEL,
    PLUGINS_LABEL,
    STARTED_LABEL,
    AnswerForm,
    EditQuestionForm,
    NewQuestionForm,
    WatchQuestionForm,
)
from kitsune.questions.models import (
    AAQConfig,
    Answer,
    AnswerVote,
    Question,
    QuestionVote,
)
from kitsune.questions.utils import (
    get_ga_submit_event_parameters_as_json,
    get_mobile_product_from_ua,
)
from kitsune.sumo.decorators import ratelimit
from kitsune.sumo.i18n import split_into_language_and_path
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import (
    build_paged_url,
    get_next_url,
    has_aaq_config,
    is_ratelimited,
    paginate,
    set_aaq_context,
    simple_paginate,
)
from kitsune.tags.models import SumoTag
from kitsune.tags.utils import add_existing_tag
from kitsune.tidings.events import ActivationRequestFailed
from kitsune.tidings.models import Watch
from kitsune.upload.models import ImageAttachment
from kitsune.users.models import Setting
from kitsune.wiki.facets import topics_for
from kitsune.wiki.utils import build_topics_data, get_featured_articles, get_kb_visited

log = logging.getLogger("k.questions")


UNAPPROVED_TAG = _lazy("That tag does not exist.")
NO_TAG = _lazy("Please provide a tag.")
IMG_LIMIT = settings.IMAGE_ATTACHMENT_USER_LIMIT

FILTER_GROUPS = {
    "all": OrderedDict(
        [
            # L10n: This is a question filter option for the All tab.
            ("recently-unanswered", _lazy("Recently unanswered")),
        ]
    ),
    "needs-attention": OrderedDict(
        [
            # L10n: This is a question filter option for the Attention needed tab.
            ("new", _lazy("New")),
            # L10n: This is a question filter option for the Attention needed tab.
            ("unhelpful-answers", _lazy("Answers didn't help")),
        ]
    ),
    "responded": OrderedDict(
        [
            # L10n: This is a question filter option for the Responded tab.
            ("needsinfo", _lazy("Needs info")),
        ]
    ),
    "done": OrderedDict(
        [
            # L10n: This is a question filter option for the Done tab.
            ("solved", _lazy("Solved")),
            # L10n: This is a question filter option for the Done tab.
            ("locked", _lazy("Locked")),
        ]
    ),
    "spam": OrderedDict(
        [
            # L10n: This is a question filter option for the Spam tab, thus "marked" refers to "marked as spam".
            ("detected-spam", _lazy("Marked automatically")),
            # L10n: This is a question filter option for the Spam tab, thus "marked" refers to "marked as spam".
            ("undetected-spam", _lazy("Marked manually")),
        ]
    ),
}

ORDER_BY = OrderedDict(
    [
        # L10n: This is a question sort option. It is a part of a drop-down menu with no heading.
        ("updated", ("updated", _lazy("Updated"))),
        # L10n: This is a question sort option. It is a part of a drop-down menu with no heading.
        ("views", ("questionvisits__visits", _lazy("Views"))),
        # L10n: This is a question sort option. It is a part of a drop-down menu with no heading.
        ("votes", ("num_votes_past_week", _lazy("Votes"))),
        # L10n: This is a question sort option. It is a part of a drop-down menu with no heading.
        ("replies", ("num_answers", _lazy("Replies"))),
    ]
)


def product_list(request):
    """View to select a product to see related questions."""
    return render(
        request,
        "questions/product_list.html",
        {"products": Product.active.with_question_forums(request.LANGUAGE_CODE)},
    )


def question_list(request, product_slug=None, topic_slug=None):
    """View the list of questions."""
    redirect_response = get_product_redirect_response(
        product_slug, question_list, topic_slug=topic_slug
    )
    if redirect_response:
        return redirect_response

    if settings.DISABLE_QUESTIONS_LIST_GLOBAL:
        messages.add_message(request, messages.WARNING, "You cannot list questions at this time.")
        return HttpResponseRedirect("/")

    topic_navigation = any(
        [
            request.resolver_match.url_name == "questions.list_by_topic",
            topic_slug and not product_slug,
        ]
    )
    filter_ = request.GET.get("filter")
    owner = request.GET.get("owner", request.session.get("questions_owner", "all"))
    show = request.GET.get("show")
    # Show defaults to NEEDS ATTENTION
    if show not in FILTER_GROUPS:
        show = "needs-attention"

    tagged = request.GET.get("tagged")
    tags = None
    topic_slug = request.GET.get("topic", "") or topic_slug

    order = request.GET.get("order", "updated")
    if order not in ORDER_BY:
        order = "updated"
    sort = request.GET.get("sort", "desc")

    product_slugs = product_slug.split(",") if product_slug else []
    products = []

    if product_slugs and ("all" not in product_slugs):
        for slug in product_slugs:
            products.append(get_object_or_404(Product, slug=slug))
    else:
        # We want all products (no product filtering at all).
        if settings.DISABLE_QUESTIONS_LIST_ALL:
            messages.add_message(
                request, messages.WARNING, "You cannot list all questions at this time."
            )
            return HttpResponseRedirect("/")
        products = Product.active.with_question_forums(request.LANGUAGE_CODE)

    multiple = (len(products) > 1) or ("all" in product_slugs)
    product_with_aaq = False
    if products and not multiple:
        product_with_aaq = has_aaq_config(products[0])

    topics = []

    if topic_slug:
        try:
            topic_history = TopicSlugHistory.objects.get(slug=topic_slug)

            return redirect(question_list, topic_slug=topic_history.topic.slug)
        except TopicSlugHistory.DoesNotExist:
            ...
        topics = Topic.active.filter(visible=True, slug=topic_slug)
        if not topics:
            raise Http404()

    question_qs = Question.objects

    if filter_ not in FILTER_GROUPS[show]:
        filter_ = None

    match filter_:
        case "new":
            question_qs = question_qs.new()
        case "unhelpful-answers":
            question_qs = question_qs.unhelpful_answers()
        case "needsinfo":
            question_qs = question_qs.needs_info()
        case "solved":
            question_qs = question_qs.solved()
        case "locked":
            question_qs = question_qs.locked()
        case "recently-unanswered":
            question_qs = question_qs.recently_unanswered()
        case "detected-spam":
            question_qs = question_qs.detected_spam()
        case "undetected-spam":
            question_qs = question_qs.undetected_spam()
        case _:
            if show == "needs-attention":
                question_qs = question_qs.needs_attention()
            if show == "responded":
                question_qs = question_qs.responded()
            if show == "done":
                question_qs = question_qs.done()
            if show == "spam":
                question_qs = question_qs.spam()

    question_qs = question_qs.select_related(
        "creator",
        "last_answer",
        "last_answer__creator",
        "solution",
        "solution__creator",
        "topic",
        "product",
    )
    # Exclude questions over 90 days old without an answer or older than 2 years or created
    # by deactivated users. Use "__range" to ensure the database index is used in Postgres.
    today = date.today()
    question_qs = (
        question_qs.exclude(
            created__range=(datetime.min, today - timedelta(days=90)), num_answers=0
        )
        .filter(creator__is_active=True)
        .filter(updated__range=(today - timedelta(days=365 * 2), Now()))
    )

    question_qs = question_qs.prefetch_related("tags")

    # Annotate with visit counts to avoid N+1 queries
    question_qs = question_qs.annotate(visits_count=F("questionvisits__visits"))

    if not request.user.has_perm("flagit.can_moderate") or show != "spam":
        question_qs = question_qs.filter(is_spam=False)

    if owner == "mine" and request.user.is_authenticated:
        criteria = Q(answers__creator=request.user) | Q(creator=request.user)
        question_qs = question_qs.filter(criteria).distinct()
    else:
        owner = None

    # Annotate with is_contributor for authenticated users to avoid N+1 queries
    if request.user.is_authenticated:
        contributor_subquery = Answer.objects.filter(question=OuterRef("pk"), creator=request.user)
        question_qs = question_qs.annotate(
            user_is_contributor=Exists(contributor_subquery) | Q(creator=request.user)
        )

    feed_urls = (
        (
            urlparams(reverse("questions.feed"), product=product_slug, topic=topic_slug),
            QuestionsFeed().title(),
        ),
    )

    if tagged:
        tag_slugs = tagged.split(",")
        tags = SumoTag.objects.active().filter(slug__in=tag_slugs)
        if tags:
            for t in tags:
                question_qs = question_qs.filter(tags__name__in=[t.name])
            if len(tags) == 1:
                feed_urls += (
                    (
                        reverse("questions.tagged_feed", args=[tags[0].slug]),
                        TaggedQuestionsFeed().title(tags[0]),
                    ),
                )
        else:
            question_qs = Question.objects.none()

    # Filter by products.
    if products:
        question_qs = question_qs.filter(product__in=products)

    # Filter by topic.
    if topics:
        # This filter will match if any of the topics on a question have the
        # correct id.
        question_qs = question_qs.filter(topic__in=topics)

    # Filter by locale for AAQ locales, and by locale + default for others.
    if request.LANGUAGE_CODE in AAQConfig.objects.locales_list():
        locale_query = Q(locale=request.LANGUAGE_CODE)
    else:
        locale_query = Q(locale=request.LANGUAGE_CODE)
        locale_query |= Q(locale=settings.WIKI_DEFAULT_LANGUAGE)

    question_qs = question_qs.filter(locale_query)

    # Set the order.
    # Set a default value if a user requested a non existing order parameter
    order_by = ORDER_BY.get(order, ["updated"])[0]

    # Use Django's built-in NULL sorting features
    if sort == "asc":
        order_by_expression = F(order_by).asc(nulls_first=True)
    else:
        order_by_expression = F(order_by).desc(nulls_last=True)

    question_qs = question_qs.order_by(order_by_expression)

    try:
        questions_page = simple_paginate(request, question_qs, per_page=config.QUESTIONS_PER_PAGE)
    except (PageNotAnInteger, EmptyPage):
        # If we aren't on page 1, redirect there.
        # TODO: Is 404 more appropriate?
        if request.GET.get("page", "1") != "1":
            url = build_paged_url(request)
            return HttpResponseRedirect(urlparams(url, page=1))

    # Recent answered stats
    extra_filters = locale_query

    if products:
        extra_filters &= Q(product__in=products)

    recent_asked_count = Question.recent_asked_count(extra_filters)
    recent_unanswered_count = Question.recent_unanswered_count(extra_filters)
    if recent_asked_count:
        recent_answered_percent = int(
            (float(recent_asked_count - recent_unanswered_count) / recent_asked_count) * 100
        )
    else:
        recent_answered_percent = 0

    # List of products to fill the selector.
    product_list = Product.active.filter(visible=True)

    # List of topics to fill the selector.
    topic_list = Topic.active.filter(in_aaq=True, visible=True)
    if product_slugs:
        topic_list = topic_list.filter(products__in=products).distinct()
    else:
        topic_list = topic_list.filter(in_nav=True)

    # Store current filters in the session
    if request.user.is_authenticated:
        request.session["questions_owner"] = owner

    data = {
        "questions": questions_page,
        "feeds": feed_urls,
        "filter": filter_,
        "owner": owner,
        "show": show,
        "filters": FILTER_GROUPS[show],
        "order": order,
        "orders": ORDER_BY,
        "sort": sort,
        "tags": tags,
        "tagged": tagged,
        "recent_asked_count": recent_asked_count,
        "recent_unanswered_count": recent_unanswered_count,
        "recent_answered_percent": recent_answered_percent,
        "product_list": product_list,
        "products": products,
        "topic_slug": topic_slug,
        "multiple_products": multiple,
        "all_products": product_slug == "all" or topic_navigation,
        "topic_list": topic_list,
        "topics": topics,
        "selected_topic_slug": topics[0].slug if topics else None,
        "product_slug": product_slug,
        "topic_navigation": topic_navigation,
        "has_aaq_config": product_with_aaq,
    }

    if products:
        data["ga_products"] = f"/{'/'.join(product.slug for product in products)}/"

    return render(request, "questions/question_list.html", data)


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
        (("accessibility",), dict),
        (("accessibility", "isActive"), bool),
        (("application",), dict),
        (("application", "name"), str),
        (("application", "supportURL"), str),
        (("application", "userAgent"), str),
        (("application", "version"), str),
        (("extensions",), list),
        (("graphics",), dict),
        (("javaScript",), dict),
        (("modifiedPreferences",), dict),
        (("userJS",), dict),
        (("userJS", "exists"), bool),
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

    parsed["modifiedPreferences"] = {
        key: val
        for (key, val) in list(parsed["modifiedPreferences"].items())
        if not key.startswith("print")
    }

    return parsed


def question_details(
    request, question_id, form=None, watch_form=None, answer_preview=None, **extra_kwargs
):
    """View the answers to a question."""
    ans_ = _answers_data(request, question_id, form, watch_form, answer_preview)
    question = ans_["question"]
    set_aaq_context(request, question.product)

    if question.is_spam and not request.user.has_perm("flagit.can_moderate"):
        raise Http404("No question matches the given query.")

    # Try to parse troubleshooting data as JSON.
    troubleshooting_json = question.metadata.get("troubleshooting")
    question.metadata["troubleshooting_parsed"] = parse_troubleshooting(troubleshooting_json)

    if request.user.is_authenticated:
        ct = ContentType.objects.get_for_model(request.user)
        ans_["images"] = list(
            ImageAttachment.objects.filter(creator=request.user, content_type=ct)
            .only("id", "creator_id", "file", "thumbnail")
            .order_by("-id")[:IMG_LIMIT]
        )

    extra_kwargs.update(ans_)

    products = Product.active.with_question_forums(request.LANGUAGE_CODE)
    # Use get_hierarchical_topics instead of topics_for to match the moderate view
    topics = get_hierarchical_topics(question.product) if question.product else []

    related_documents = question.related_documents
    related_questions = question.related_questions
    question_images = question.get_images()

    extra_kwargs.update(
        {
            "all_products": products,
            "all_topics": topics,
            "all_tags": SumoTag.objects.active(),
            "related_documents": related_documents,
            "related_questions": related_questions,
            "question_images": question_images,
        }
    )

    # Add noindex to questions without a solution.
    if not question.solution_id:
        extra_kwargs.update(robots_noindex=True)

    if request.session.pop("aaq-final-step", False):
        extra_kwargs.update({"aaq_final_step": True})

    return render(request, "questions/question_details.html", extra_kwargs)


@require_POST
@permission_required("questions.change_question")
def edit_details(request, question_id):
    try:
        product = Product.active.get(id=request.POST.get("product"))
        topic = Topic.active.get(id=request.POST.get("topic"), products=product)
        locale = request.POST.get("locale")

        # If locale is not in AAQ_LANGUAGES throws a ValueError
        tuple(AAQConfig.objects.locales_list()).index(locale)
    except (Product.DoesNotExist, Topic.DoesNotExist, ValueError):
        return HttpResponseBadRequest()

    question = get_object_or_404(Question, pk=question_id)
    existing_tags = SumoTag.objects.active().filter(
        Q(name=question.topic.slug) | Q(name=question.product.slug)
    )
    question.tags.remove(*existing_tags)
    question.product = product
    question.topic = topic
    question.locale = locale
    question.save()
    question.auto_tag()
    question.clear_cached_tags()
    return redirect(reverse("questions.details", kwargs={"question_id": question_id}))


def aaq_location_proxy(request):
    """Proxy request from the Mozilla service to our form."""
    response = requests.get(settings.MOZILLA_LOCATION_SERVICE)
    return JsonResponse(response.json())


def aaq(request, product_slug=None, step=1, is_loginless=False):
    """Ask a new question."""
    # After the migration to a DB based AAQ, we need to account for
    # product slugs that were not present in the questions config.
    should_redirect = True
    match product_slug:
        case "desktop":
            product_slug = "firefox"
        case "focus":
            product_slug = "focus-firefox"
        case _:
            should_redirect = False

    if should_redirect:
        return HttpResponsePermanentRedirect(reverse("questions.aaq_step2", args=[product_slug]))

    template = "questions/new_question.html"

    # Check if the user is using a mobile device,
    # render step 2 if they are
    product_slug = product_slug or request.GET.get("product")
    if product_slug is None:
        change_product = False
        if request.GET.get("q") == "change_product":
            change_product = True

        is_mobile_device = get_user_agent(request).is_mobile

        if is_mobile_device and not change_product:
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            if product_slug := get_mobile_product_from_ua(user_agent):
                # redirect needed for InAAQMiddleware
                step_2 = reverse("questions.aaq_step2", args=[product_slug])
                return HttpResponseRedirect(step_2)

    # Return 404 if the products does not have an AAQ form or if it is archived
    product = None
    products_with_aaqs = Product.active.filter(aaq_configs__is_active=True).distinct()
    if product_slug:
        try:
            product = Product.active.get(slug=product_slug)
        except Product.DoesNotExist:
            raise Http404
        else:
            if product not in products_with_aaqs:
                raise Http404

    context = {
        "products": products_with_aaqs,
        "current_product": product,
        "current_step": step,
        "host": Site.objects.get_current().domain,
        "is_loginless": is_loginless,
        "ga_content_group": f"aaq-step-{step}",
    }
    # If the selected product doesn't exist in DB, render a 404
    if step > 1:
        set_aaq_context(request, product)
        has_public_forum = product.questions_enabled(locale=request.LANGUAGE_CODE)
        context["has_ticketing_support"] = product.has_ticketing_support
        context["ga_products"] = f"/{product_slug}/"

    if step == 2:
        topics = topics_for(request.user, product, parent=None)

        context["featured"] = get_featured_articles(
            product=product, locale=request.LANGUAGE_CODE, fetch_for_aaq=True
        )
        context["topics"] = build_topics_data(request, product, topics)

    elif step == 3:
        context["cancel_url"] = get_next_url(request) or (
            reverse("products.product", args=[product.slug])
            if is_loginless
            else reverse("questions.aaq_step2", args=[product_slug])
        )

        # Check if the selected product has a forum in the user's locale
        if not has_public_forum:
            locale, path = split_into_language_and_path(request.path_info)
            path = f"/{settings.WIKI_DEFAULT_LANGUAGE}{path}"

            old_lang = settings.LANGUAGES_DICT[request.LANGUAGE_CODE.lower()]
            new_lang = settings.LANGUAGES_DICT[settings.WIKI_DEFAULT_LANGUAGE.lower()]
            msg = _(
                "The questions forum isn't available for {product} in {old_lang}, we "
                "have redirected you to the {new_lang} questions forum."
            ).format(product=product.title, old_lang=old_lang, new_lang=new_lang)
            messages.add_message(request, messages.WARNING, msg)

            return HttpResponseRedirect(path)

        if product.has_ticketing_support:
            zendesk_form = ZendeskForm(
                data=request.POST or None,
                product=product,
                user=request.user,
            )
            context["form"] = zendesk_form
            context["submit_event_parameters"] = get_ga_submit_event_parameters_as_json(
                request.session, product
            )

            if zendesk_form.is_valid() and not is_ratelimited(request, "loginless", "3/d"):
                zendesk_form.send(request.user, product)
                email = zendesk_form.cleaned_data["email"]

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _(
                        "Thank you for reaching out to Mozilla Support. "
                        "We're reviewing your submission and will send a confirmation email to {email} shortly."
                    ).format(email=email),
                )

                url = reverse("products.product", args=[product.slug])
                return HttpResponseRedirect(url)

            if getattr(request, "limited", False):
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("You've exceeded the number of submissions for today."),
                )

            return render(request, template, context)

        form = NewQuestionForm(
            product=product,
            data=request.POST or None,
        )
        context["form"] = form

        if form.is_valid() and not is_ratelimited(request, "aaq-day", "5/d"):
            question = form.save(
                user=request.user,
                locale=request.LANGUAGE_CODE,
                product=product,
            )

            if visits := get_kb_visited(request.session, product, question.topic):
                question.add_metadata(kb_visits_prior=json.dumps(visits))

            if form.cleaned_data.get("is_spam"):
                _add_to_moderation_queue(request, question)

            # Submitting the question counts as a vote
            question_vote(request, question.id)

            my_questions_url = reverse("users.questions", args=[request.user.username])
            messages.add_message(
                request,
                messages.SUCCESS,
                _(
                    "Done! Your question is now posted on the Mozilla community support forum. "
                    + "You can see your post anytime by visiting the {a_open}My Questions"
                    + "{a_close} page in your profile."
                ).format(a_open="<a href='" + my_questions_url + "'>", a_close="</a>"),
                extra_tags="safe",
            )

            request.session["aaq-final-step"] = True

            url = reverse("questions.details", kwargs={"question_id": question.id})
            return HttpResponseRedirect(url)

        if getattr(request, "limited", False):
            raise PermissionDenied

        user_ct = ContentType.objects.get_for_model(request.user)
        context["images"] = ImageAttachment.objects.filter(
            creator=request.user,
            content_type=user_ct,
        ).order_by("-id")[:IMG_LIMIT]

        if form.is_bound and (topic := form.cleaned_data.get("category")):
            # We've got invalid POST data, but the topic has been provided.
            # Let's set the proper GA4 event parameters on the submit button.
            context["submit_event_parameters"] = get_ga_submit_event_parameters_as_json(
                request.session, product, topic=topic
            )
        else:
            # We don't know the topic yet, since that's set via the form, so let's
            # start by providing default GA4 event parameters for the submit button.
            context["submit_event_parameters"] = get_ga_submit_event_parameters_as_json()

    return render(request, template, context)


def aaq_step2(request, product_slug):
    """Step 2: The product is selected."""
    redirect_response = get_product_redirect_response(product_slug, aaq_step2)
    if redirect_response:
        return redirect_response

    return aaq(request, product_slug=product_slug, step=2)


def aaq_step3(request, product_slug):
    """Step 3: Show full question form."""
    redirect_response = get_product_redirect_response(product_slug, aaq_step3)
    if redirect_response:
        return redirect_response

    # This view can be called by htmx to set the GA4 event parameters on the submit
    # button of the new-question form whenever the category (topic) menu is changed.
    if ("hx-request" in request.headers) and (
        request.headers.get("hx-trigger-name") == "category"
    ):
        topic_id = request.GET.get("category")
        product = get_object_or_404(Product.active, slug=product_slug)
        topic = get_object_or_404(Topic.active.filter(products=product, in_aaq=True), pk=topic_id)
        response = HttpResponse(status=204)
        response["HX-Trigger"] = json.dumps(
            {
                "setQuestionSubmitEventParameters": {
                    "eventParameters": get_ga_submit_event_parameters_as_json(
                        request.session, product, topic=topic
                    )
                }
            }
        )
        return response

    # Since removing the @login_required decorator for MA form
    # need to catch unauthenticated, non-MA users here """
    referer = request.META.get("HTTP_REFERER", "")
    is_loginless = (product_slug in settings.LOGIN_EXCEPTIONS) and any(
        uri in referer
        for uri in settings.MOZILLA_ACCOUNT_ARTICLES
        + [
            path.removeprefix(f"/{request.LANGUAGE_CODE}")
            for path in (
                reverse("users.auth"),
                reverse("questions.aaq_step3", args=[product_slug]),
            )
        ]
    )

    if not (is_loginless or request.user.is_authenticated):
        return redirect_to_login(next=request.path, login_url=reverse("users.login"))

    return aaq(
        request,
        is_loginless=is_loginless,
        product_slug=product_slug,
        step=3,
    )


@require_http_methods(["GET", "POST"])
@login_required
def edit_question(request, question_id):
    """Edit a question."""
    question = get_object_or_404(Question, pk=question_id)
    user = request.user

    if not question.allows_edit(user):
        raise PermissionDenied

    ct = ContentType.objects.get_for_model(question)
    images = ImageAttachment.objects.filter(content_type=ct, object_id=question.pk)

    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.method == "POST":
        data = json.loads(request.body)
        new_topic_id = data.get("topic")
        try:
            new_topic = Topic.objects.get(id=new_topic_id)
        except Topic.DoesNotExist:
            return JsonResponse({"error": "Topic not found"}, status=404)

        if new_topic != question.topic:
            existing_tags = SumoTag.objects.active().filter(name=question.topic.slug)
            question.tags.remove(*existing_tags)
            question.topic = new_topic
            question.update_topic_counter += 1
            question.save()
            question.auto_tag()
            question.clear_cached_tags()

        return JsonResponse({"updated_topic": str(new_topic)})

    initial_data = {
        "title": question.title,
        "content": question.content,
        **question.metadata,
    }

    form = EditQuestionForm(
        data=request.POST or None,
        product=question.product,
        initial=initial_data,
    )

    if form.is_valid():
        question.title = form.cleaned_data["title"]
        question.content = form.cleaned_data["content"]
        question.updated_by = user
        question.save(update=True)

        if form.cleaned_data.get("is_spam"):
            _add_to_moderation_queue(request, question)

        # TODO: Factor all this stuff up from here and new_question into
        # the form, which should probably become a ModelForm.
        question.clear_mutable_metadata()
        question.add_metadata(**form.cleaned_metadata)

        return HttpResponseRedirect(
            reverse("questions.details", kwargs={"question_id": question.id})
        )

    context = {
        "question": question,
        "form": form,
        "images": images,
        "current_product": question.product,
    }

    return render(request, "questions/edit_question.html", context)


@require_POST
@login_required
@ratelimit("answer-min", "4/m")
@ratelimit("answer-day", "100/d")
def reply(request, question_id):
    """Post a new answer to a question."""
    question = get_object_or_404(Question, pk=question_id, is_spam=False)
    answer_preview = None

    if not question.allows_new_answer(request.user):
        raise PermissionDenied

    form = AnswerForm(request.POST, **{"user": request.user, "question": question})

    if form.is_valid() and not request.limited:
        answer = Answer(
            question=question,
            creator=request.user,
            content=form.cleaned_data["content"],
        )
        if "preview" in request.POST:
            answer_preview = answer
        else:
            if form.cleaned_data.get("is_spam"):
                _add_to_moderation_queue(request, answer)
            else:
                answer.save()

            ans_ct = ContentType.objects.get_for_model(answer)
            # Move over to the answer all of the images I added to the
            # reply form
            user_ct = ContentType.objects.get_for_model(request.user)
            up_images = ImageAttachment.objects.filter(creator=request.user, content_type=user_ct)
            up_images.update(content_type=ans_ct, object_id=answer.id)

            # Handle needsinfo tag
            if "needsinfo" in request.POST:
                question.set_needs_info()
            elif "clear_needsinfo" in request.POST:
                question.unset_needs_info()

            if Setting.get_for_user(request.user, "questions_watch_after_reply"):
                QuestionReplyEvent.notify(request.user, question)

            return HttpResponseRedirect(answer.get_absolute_url())

    return question_details(
        request, question_id=question_id, form=form, answer_preview=answer_preview
    )


@require_http_methods(["GET", "POST"])
def solve(request, question_id, answer_id):
    """Accept an answer as the solution to the question."""

    if not (
        ((request.method == "GET") and (watch_secret := request.GET.get("watch", None)))
        or (
            (request.method == "POST")
            and (request.user.is_authenticated and request.user.is_active)
        )
    ):
        return HttpResponseForbidden()

    question = get_object_or_404(Question, pk=question_id, is_spam=False)

    if request.method == "GET":
        # This was clicked from an email.
        try:
            watch = Watch.objects.get(
                secret=watch_secret, event_type="question reply", user=question.creator
            )
            # Create a new secret.
            distinguishable_letters = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRTUVWXYZ"
            new_secret = "".join(random.choice(distinguishable_letters) for x in range(10))
            watch.update(secret=new_secret)
            request.user = question.creator
        except Watch.DoesNotExist:
            # The provided watch secret is invalid.
            return HttpResponseForbidden()

    answer = get_object_or_404(Answer, pk=answer_id, is_spam=False)

    if not question.allows_solve(request.user):
        raise PermissionDenied

    if question.creator != request.user and not request.user.has_perm("questions.change_solution"):
        return HttpResponseForbidden()

    if not question.solution:
        question.set_solution(answer, request.user)

        messages.add_message(request, messages.SUCCESS, _("Thank you for choosing a solution!"))
    else:
        # The question was already solved.
        messages.add_message(request, messages.ERROR, _("This question already has a solution."))

    return HttpResponseRedirect(question.get_absolute_url())


@require_POST
@login_required
def unsolve(request, question_id, answer_id):
    """Accept an answer as the solution to the question."""
    question = get_object_or_404(Question, pk=question_id)
    get_object_or_404(Answer, pk=answer_id)

    if not question.allows_unsolve(request.user):
        raise PermissionDenied

    if question.creator != request.user and not request.user.has_perm("questions.change_solution"):
        return HttpResponseForbidden()

    question.solution = None
    question.save()

    messages.add_message(request, messages.SUCCESS, _("The solution was undone successfully."))

    return HttpResponseRedirect(question.get_absolute_url())


@require_POST
@ratelimit("question-vote", "1/h")
def question_vote(request, question_id):
    """I have this problem too."""
    question = get_object_or_404(Question, pk=question_id, is_spam=False)

    if not question.editable:
        raise PermissionDenied

    if not question.has_voted(request):
        vote = QuestionVote(question=question)

        if request.user.is_authenticated:
            vote.creator = request.user
        else:
            vote.anonymous_id = request.anonymous.anonymous_id

        if not request.limited:
            vote.save()

            if "referrer" in request.GET:
                referrer = request.GET.get("referrer")
                vote.add_metadata("referrer", referrer)

                if referrer == "search" and "query" in request.GET:
                    vote.add_metadata("query", request.GET.get("query"))

            ua = request.META.get("HTTP_USER_AGENT")
            if ua:
                vote.add_metadata("ua", ua)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            tmpl = "questions/includes/question_vote_thanks.html"
            form = _init_watch_form(request)
            html = render_to_string(
                tmpl,
                {
                    "question": question,
                    "user": request.user,
                    "watch_form": form,
                },
            )

            return HttpResponse(json.dumps({"html": html, "ignored": request.limited}))

    return HttpResponseRedirect(question.get_absolute_url())


@require_POST
@login_required
@ratelimit("answer-vote", "1/h")
def answer_vote(request, question_id, answer_id):
    """Vote for Helpful/Not Helpful answers"""
    answer = get_object_or_404(
        Answer,
        pk=answer_id,
        question=question_id,
        is_spam=False,
        question__is_spam=False,
    )

    if not answer.question.editable:
        raise PermissionDenied

    if request.limited:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return HttpResponse(json.dumps({"ignored": True}))
        else:
            return HttpResponseRedirect(answer.get_absolute_url())

    if not answer.has_voted(request):
        vote = AnswerVote(answer=answer, creator=request.user)

        if "helpful" in request.POST:
            vote.helpful = True
            message = _("Glad to hear it!")
        else:
            message = _("Sorry to hear that.")

        vote.save()

        if "referrer" in request.GET:
            referrer = request.GET.get("referrer")
            vote.add_metadata("referrer", referrer)

            if referrer == "search" and "query" in request.GET:
                vote.add_metadata("query", request.GET.get("query"))

        ua = request.META.get("HTTP_USER_AGENT")
        if ua:
            vote.add_metadata("ua", ua)
    else:
        message = _("You already voted on this reply.")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return HttpResponse(json.dumps({"message": message}))

    return HttpResponseRedirect(answer.get_absolute_url())


@permission_required("questions.tag_question")
def add_tag(request, question_id):
    """Add a (case-insensitive) tag to question.

    If the question already has the tag, do nothing.

    """
    # If somebody hits Return in the address bar after provoking an error from
    # the add form, nicely send them back to the question:
    if request.method == "GET":
        return HttpResponseRedirect(reverse("questions.details", args=[question_id]))

    try:
        question, canonical_name = _add_tag(request, question_id)
    except SumoTag.DoesNotExist:
        template_data = _answers_data(request, question_id)
        template_data["tag_adding_error"] = UNAPPROVED_TAG
        template_data["tag_adding_value"] = request.POST.get("tag-name", "")
        return render(request, "questions/question_details.html", template_data)

    if canonical_name:  # success
        question.clear_cached_tags()
        return HttpResponseRedirect(reverse("questions.details", args=[question_id]))

    # No tag provided
    template_data = _answers_data(request, question_id)
    template_data["tag_adding_error"] = NO_TAG
    return render(request, "questions/question_details.html", template_data)


@permission_required("questions.tag_question")
@require_POST
def add_tag_async(request, question_id):
    """Add a (case-insensitive) tag to question asyncronously. Return empty.

    If the question already has the tag, do nothing.
    """

    if request.content_type == "application/json":
        tag_ids = json.loads(request.body).get("tags", [])
        question, tags = _add_tag(request, question_id, tag_ids)
        question.clear_cached_tags()
        if not tags:
            return JsonResponse({"error": "Some tags do not exist or are invalid"}, status=400)
        return JsonResponse({"message": "Tags updated successfully.", "data": {"tags": tags}})

    try:
        question, canonical_name = _add_tag(request, question_id)
    except SumoTag.DoesNotExist:
        return HttpResponse(
            json.dumps({"error": str(UNAPPROVED_TAG)}), content_type="application/json", status=400
        )

    if canonical_name:
        question.clear_cached_tags()
        tag = SumoTag.objects.get(name=canonical_name)
        tag_url = urlparams(
            reverse("questions.list", args=[question.product_slug]), tagged=tag.slug
        )
        data = {"canonicalName": canonical_name, "tagUrl": tag_url}
        return HttpResponse(json.dumps(data), content_type="application/json")

    return HttpResponse(
        json.dumps({"error": str(NO_TAG)}), content_type="application/json", status=400
    )


@permission_required("questions.tag_question")
@require_POST
def remove_tag(request, question_id):
    """Remove a (case-insensitive) tag from question.

    Expects a POST with the tag name embedded in a field name, like
    remove-tag-tagNameHere. If question doesn't have that tag, do nothing.

    """
    prefix = "remove-tag-"
    names = [k for k in request.POST if k.startswith(prefix)]
    if names:
        name = names[0][len(prefix) :]
        question = get_object_or_404(Question, pk=question_id)
        question.tags.remove(name)
        question.clear_cached_tags()

    return HttpResponseRedirect(reverse("questions.details", args=[question_id]))


@permission_required("questions.tag_question")
@require_POST
def remove_tag_async(request, question_id):
    """Remove a (case-insensitive) tag from question.

    If question doesn't have that tag, do nothing. Return value is JSON.

    """

    question = get_object_or_404(Question, pk=question_id)
    if request.content_type == "application/json":
        data = json.loads(request.body)
        tag_id = data.get("tagId")

        try:
            tag = SumoTag.objects.get(id=tag_id)
        except SumoTag.DoesNotExist:
            return JsonResponse({"error": "Tag does not exist."}, status=400)

        question.tags.remove(tag)
        question.clear_cached_tags()
        return JsonResponse({"message": f"Tag '{tag.name}' removed successfully."})

    name = request.POST.get("name")
    if name:
        question.tags.remove(name)
        question.clear_cached_tags()
        return HttpResponse("{}", content_type="application/json")
    return HttpResponseBadRequest(
        json.dumps({"error": str(NO_TAG)}), content_type="application/json"
    )


@permission_required("flagit.can_moderate")
@require_POST
def mark_spam(request):
    """Mark a question or an answer as spam"""
    if request.POST.get("question_id"):
        question_id = request.POST.get("question_id")
        obj = get_object_or_404(Question, pk=question_id)
    else:
        answer_id = request.POST.get("answer_id")
        obj = get_object_or_404(Answer, pk=answer_id)
        question_id = obj.question.id

    obj.mark_as_spam(request.user)

    return HttpResponseRedirect(reverse("questions.details", kwargs={"question_id": question_id}))


@permission_required("flagit.can_moderate")
@require_POST
def unmark_spam(request):
    """Mark a question or an answer as spam"""
    if request.POST.get("question_id"):
        question_id = request.POST.get("question_id")
        obj = get_object_or_404(Question, pk=question_id)
    else:
        answer_id = request.POST.get("answer_id")
        obj = get_object_or_404(Answer, pk=answer_id)
        question_id = obj.question.id

    obj.is_spam = False
    obj.marked_as_spam = None
    obj.marked_as_spam_by = None
    obj.save()

    return HttpResponseRedirect(reverse("questions.details", kwargs={"question_id": question_id}))


@login_required
def delete_question(request, question_id):
    """Delete a question"""
    question = get_object_or_404(Question, pk=question_id)

    if not question.allows_delete(request.user):
        raise PermissionDenied

    if request.method == "GET":
        # Render the confirmation page
        return render(request, "questions/confirm_question_delete.html", {"question": question})

    # Capture the product slug to build the questions.list url below.
    product = question.product_slug

    # Handle confirm delete form POST
    log.warning("User {} is deleting question with id={}".format(request.user, question.id))
    question.delete()

    return HttpResponseRedirect(reverse("questions.list", args=[product]))


@login_required
def delete_answer(request, question_id, answer_id):
    """Delete an answer"""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)

    if not answer.allows_delete(request.user):
        raise PermissionDenied

    if request.method == "GET":
        # Render the confirmation page
        return render(request, "questions/confirm_answer_delete.html", {"answer": answer})

    # Handle confirm delete form POST
    log.warning("User {} is deleting answer with id={}".format(request.user, answer.id))
    answer.delete()

    return HttpResponseRedirect(reverse("questions.details", args=[question_id]))


@require_POST
@login_required
def lock_question(request, question_id):
    """Lock or unlock a question"""
    question = get_object_or_404(Question, pk=question_id)

    if not question.allows_lock(request.user):
        raise PermissionDenied

    question.is_locked = not question.is_locked
    log.info(
        "User {} set is_locked={} on question with id={} ".format(
            request.user, question.is_locked, question.id
        )
    )
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
    log.info(
        "User {} set is_archived={} on question with id={} ".format(
            request.user, question.is_archived, question.id
        )
    )
    question.save()

    return HttpResponseRedirect(question.get_absolute_url())


@login_required
def edit_answer(request, question_id, answer_id):
    """Edit an answer."""
    answer = get_object_or_404(Answer, pk=answer_id, question=question_id)
    answer_preview = None

    if not answer.allows_edit(request.user):
        raise PermissionDenied

    if request.method == "GET":
        form = AnswerForm({"content": answer.content}, user=request.user)
        return render(request, "questions/edit_answer.html", {"form": form, "answer": answer})

    form = AnswerForm(request.POST, **{"user": request.user})

    if form.is_valid():
        answer.content = form.cleaned_data["content"]
        answer.updated_by = request.user
        if "preview" in request.POST:
            answer.updated = datetime.now()
            answer_preview = answer
        else:
            log.warning("User {} is editing answer with id={}".format(request.user, answer.id))

            if form.cleaned_data.get("is_spam"):
                _add_to_moderation_queue(request, answer)
            else:
                answer.save()

            return HttpResponseRedirect(answer.get_absolute_url())

    return render(
        request,
        "questions/edit_answer.html",
        {"form": form, "answer": answer, "answer_preview": answer_preview},
    )


@require_POST
@ratelimit("watch-question", "10/d")
def watch_question(request, question_id):
    """Start watching a question for replies or solution."""

    if request.limited:
        msg = _(
            "We were unable to register your request. You've exceeded the "
            "limit for the number of questions allowed to watch in a day. "
            "Please try again tomorrow."
        )
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return HttpResponse(json.dumps({"message": msg, "ignored": True}))

        messages.add_message(request, messages.ERROR, msg)
        return HttpResponseRedirect(
            reverse("questions.details", kwargs={"question_id": question_id})
        )

    question = get_object_or_404(Question, pk=question_id, is_spam=False)

    form = WatchQuestionForm(request.user, request.POST)

    # Process the form
    msg = None
    if form.is_valid():
        user_or_email = (
            request.user if request.user.is_authenticated else form.cleaned_data["email"]
        )
        try:
            if form.cleaned_data["event_type"] == "reply":
                QuestionReplyEvent.notify(user_or_email, question)
            else:
                QuestionSolvedEvent.notify(user_or_email, question)
        except ActivationRequestFailed:
            msg = _("Could not send a message to that email address.")

    # Respond to ajax request
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if form.is_valid():
            msg = msg or (
                _("You will be notified of updates by email.")
                if request.user.is_authenticated
                else _("You should receive an email shortly to confirm your subscription.")
            )
            return HttpResponse(json.dumps({"message": msg}))

        if request.POST.get("from_vote"):
            tmpl = "questions/includes/question_vote_thanks.html"
        else:
            tmpl = "questions/includes/email_subscribe.html"

        html = render_to_string(
            tmpl, context={"question": question, "watch_form": form}, request=request
        )
        return HttpResponse(json.dumps({"html": html}))

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

    return render(
        request,
        "questions/unsubscribe_watch.html",
        {"question": question, "success": success},
    )


@require_GET
def activate_watch(request, watch_id, secret):
    """Activate watching a question."""
    watch = get_object_or_404(Watch, pk=watch_id)
    question = watch.content_object
    if watch.secret == secret and isinstance(question, Question):
        watch.activate().save()

    return render(
        request,
        "questions/activate_watch.html",
        {
            "question": question,
            "unsubscribe_url": reverse("questions.unsubscribe", args=[watch_id, secret]),
            "is_active": watch.is_active,
        },
    )


@login_required
@require_POST
def answer_preview_async(request):
    """Create an HTML fragment preview of the posted wiki syntax."""
    answer = Answer(creator=request.user, content=request.POST.get("content", ""))
    template = "questions/includes/answer_preview.html"

    question_id = request.POST.get("slug", "").split("/")[-1]
    question = None

    if question_id and question_id.isdigit():
        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            pass

    return render(request, template, {"answer_preview": answer, "question": question})


def metrics(request, locale_code=None):
    """The Support Forum metrics dashboard."""
    template = "questions/metrics.html"

    product = request.GET.get("product")
    if product:
        product = get_object_or_404(Product, slug=product)

    data = {
        "current_locale": locale_code,
        "product": product,
        "products": Product.active.filter(visible=True),
    }

    return render(request, template, data)


def _answers_data(request, question_id, form=None, watch_form=None, answer_preview=None):
    """Return a map of the minimal info necessary to draw an answers page."""
    question = get_object_or_404(
        Question.objects.select_related(
            "creator",
            "updated_by",
            "last_answer",
            "last_answer__creator",
            "solution",
            "marked_as_spam_by",
            "taken_by",
            "product",
            "topic",
        ).prefetch_related("tags", "metadata_set"),
        pk=question_id,
    )
    answers_ = question.answers.all()

    # Remove spam flag if an answer passed the moderation queue
    if not settings.READ_ONLY:
        answers_.filter(flags__status=2).update(is_spam=False)

    if not request.user.has_perm("flagit.can_moderate"):
        answers_ = answers_.filter(is_spam=False)

    answers_ = paginate(request, answers_, per_page=config.ANSWERS_PER_PAGE)
    feed_urls = (
        (
            reverse("questions.answers.feed", kwargs={"question_id": question_id}),
            AnswersFeed().title(question),
        ),
    )

    frequencies = dict(FREQUENCY_CHOICES)

    is_watching_question = request.user.is_authenticated and (
        QuestionReplyEvent.is_notifying(request.user, question)
        or QuestionSolvedEvent.is_notifying(request.user, question)
    )

    # Sort the tags without modifying the query, so we ensure that
    # the prefetch cache is used.
    tags = sorted(question.tags.all(), key=lambda t: t.name)

    return {
        "question": question,
        "product": question.product,
        "topic": question.topic,
        "answers": answers_,
        "form": form or AnswerForm(),
        "answer_preview": answer_preview,
        "watch_form": watch_form or _init_watch_form(request, "reply"),
        "feeds": feed_urls,
        "crash_id_label": CRASH_ID_LABEL,
        "frequency_label": FREQUENCY_LABEL,
        "frequencies": frequencies,
        "started_label": STARTED_LABEL,
        "plugins_label": PLUGINS_LABEL,
        "is_watching_question": is_watching_question,
        "tags": tags,
        "tag_ids": {t.id for t in tags},
        "can_tag": request.user.has_perm("questions.tag_question"),
        "can_create_tags": request.user.has_perm("taggit.add_tag"),
    }


def _add_tag(
    request: HttpRequest, question_id: int, tag_ids: list[int] | None = None
) -> tuple[Question | None, list[str] | str | None]:
    """Add tags to a question by tag IDs or tag name.

    If tag_ids is provided, adds tags with those IDs to the question.
    Otherwise looks for tag name in request.POST['tag-name'].

    Returns a tuple of (question, tag_names) if successful.
    Returns (None, None) if no valid tags found or SumoTag.DoesNotExist raised.
    """

    question = get_object_or_404(Question, pk=question_id)
    if tag_ids:
        sumo_tags = SumoTag.objects.active().filter(id__in=tag_ids)
        if len(tag_ids) != len(sumo_tags):
            return None, None
        question.tags.add(*sumo_tags)
        return question, list(sumo_tags.values_list("name", flat=True))

    if tag_name := request.POST.get("tag-name", "").strip():
        # This raises SumoTag.DoesNotExist if the tag doesn't exist.
        canonical_name = add_existing_tag(tag_name, question.tags)

        return question, canonical_name

    return None, None


# Initialize a WatchQuestionForm
def _init_watch_form(request, event_type="solution"):
    initial = {"event_type": event_type}
    return WatchQuestionForm(request.user, initial=initial)


def _add_to_moderation_queue(request, instance):
    instance.is_spam = True
    instance.save()

    flag = FlaggedObject(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.id,
        reason="spam",
        notes="Automatically flagged at creation and marked as spam.",
        creator=request.user,
    )
    flag.save()

    messages.add_message(
        request,
        messages.WARNING,
        _("A moderator must manually approve your post before it will be visible."),
    )
