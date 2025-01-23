import json

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models.functions import Now
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from kitsune.access.decorators import group_required, login_required, permission_required
from kitsune.flagit.models import FlaggedObject
from kitsune.products.models import Product, Topic
from kitsune.questions.events import QuestionReplyEvent
from kitsune.questions.models import Answer, Question
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import paginate
from kitsune.tags.models import SumoTag


def get_flagged_objects(reason=None, exclude_reason=None, content_model=None, product_slug=None):
    """Retrieve pending flagged objects with optional filtering, eager loading related fields."""
    queryset = FlaggedObject.objects.pending().select_related("content_type", "creator")
    if exclude_reason:
        queryset = queryset.exclude(reason=exclude_reason)
    if reason:
        queryset = queryset.filter(reason=reason)
    if content_model:
        queryset = queryset.filter(content_type=content_model)
    if product_slug:
        matching_product_ids = [
            obj.id
            for obj in queryset
            if hasattr(obj.content_object, "product")
            and obj.content_object.product.slug == product_slug
        ]
        queryset = queryset.filter(id__in=matching_product_ids)
    return queryset


def set_form_action_for_objects(objects, reason=None, product_slug=None):
    """Generate form action URLs for flagged objects."""
    for obj in objects:
        base_url = reverse("flagit.update", args=[obj.id])
        obj.form_action = urlparams(base_url, reason=reason, product=product_slug)
    return objects


@require_POST
@login_required
def flag(request, content_type=None, model=None, object_id=None, **kwargs):
    if model:
        content_type = ContentType.objects.get_for_model(model).id
    content_type = content_type or request.POST.get("content_type")
    object_id = int(object_id or request.POST.get("object_id"))

    content_type = get_object_or_404(ContentType, id=int(content_type))
    content_object = get_object_or_404(content_type.model_class(), pk=object_id)

    reason = request.POST.get("reason")
    notes = request.POST.get("other", "")
    next = request.POST.get("next")

    moderation_flag_query = FlaggedObject.objects.filter(
        content_type=content_type,
        object_id=object_id,
        reason=FlaggedObject.REASON_CONTENT_MODERATION,
    ).exclude(status=FlaggedObject.FLAG_DUPLICATE)
    default_kwargs = {"content_object": content_object, "reason": reason, "notes": notes}
    if reason == FlaggedObject.REASON_CONTENT_MODERATION:
        moderation_flag_query.update(status=FlaggedObject.FLAG_PENDING)
        default_kwargs["status"] = FlaggedObject.FLAG_DUPLICATE
    else:
        moderation_flag_query.delete()

    # Check that this user hasn't already flagged the object
    _flagged, created = FlaggedObject.objects.get_or_create(
        content_type=content_type,
        object_id=object_id,
        creator=request.user,
        defaults=default_kwargs,
    )
    msg = (
        _("You already flagged this content.")
        if not created
        else _("You have flagged this content. A moderator will review your submission shortly.")
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return HttpResponse(json.dumps({"message": msg}))
    elif next:
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(next)

    return HttpResponse(msg)


@login_required
@permission_required("flagit.can_moderate")
def flagged_queue(request):
    """Display the flagged queue with optimized queries."""
    reason = request.GET.get("reason")

    objects = (
        get_flagged_objects(reason=reason, exclude_reason=FlaggedObject.REASON_CONTENT_MODERATION)
        .select_related("content_type", "creator")
        .prefetch_related("content_object")
    )
    objects = set_form_action_for_objects(objects, reason=reason)

    return render(
        request,
        "flagit/queue.html",
        {
            "objects": objects,
            "locale": request.LANGUAGE_CODE,
            "reasons": FlaggedObject.REASONS,
            "selected_reason": reason,
        },
    )


def get_hierarchical_topics(product, cache_timeout=3600):
    """
    Build hierarchical topics filtered by the given product.

    Args:
        product: The product that should be used to filter the topics.
        cache_timeout: The number of seconds to cache the result for the
                       given product. Defaults to 1 hour.

    Returns:
        A list of dictionaries representing the hierarchical structure of topics.
    """
    cache_key = f"hierarchical_topics_{product.slug}"
    if cached_topics := cache.get(cache_key):
        return cached_topics

    topics = list(
        Topic.active.filter(products=product).order_by("title").values("id", "title", "parent_id")
    )
    topic_dict = {}
    for topic in topics:
        parent_id = topic["parent_id"]
        if parent_id not in topic_dict:
            topic_dict[parent_id] = []
        topic_dict[parent_id].append(topic)

    hierarchical = []

    def build_hierarchy(parent_id=None, level=0):
        children = topic_dict.get(parent_id, [])
        for child in children:
            spaces = "&nbsp;" * (level * 4)
            hierarchical.append({"id": child["id"], "title": f"{spaces}{child['title']}"})
            build_hierarchy(child["id"], level + 1)

    build_hierarchy()
    cache.set(cache_key, hierarchical, cache_timeout)
    return hierarchical


@group_required("Content Moderators")
@require_http_methods(["GET", "POST"])
def moderate_content(request):
    """Display flagged content that needs moderation."""
    product_slug = request.GET.get("product")
    assignee = request.GET.get("assignee")

    if (
        assignee
        and not User.objects.filter(
            is_active=True, username=assignee, groups__name="Content Moderators"
        ).exists()
    ):
        return HttpResponseNotFound()

    content_type = ContentType.objects.get_for_model(Question)
    objects = (
        get_flagged_objects(
            reason=FlaggedObject.REASON_CONTENT_MODERATION,
            content_model=content_type,
            product_slug=product_slug,
        )
        .select_related("content_type", "creator", "assignee")
        .prefetch_related("content_object__product")
    )

    if request.method == "POST":
        if not (assignee and (request.user.username == assignee)):
            return HttpResponseForbidden()

        action = request.POST.get("action")
        if not (action and (action in ("assign", "unassign"))):
            return HttpResponseBadRequest()

        if action == "assign":
            # Assign another batch of objects to the user.
            assigment_qs = objects.filter(assignee__isnull=True)[:20].values_list("id", flat=True)
            objects.filter(id__in=assigment_qs).update(
                assignee=request.user, assigned_timestamp=Now()
            )
        else:
            # Unassign all of the user's objects.
            objects.filter(assignee=request.user).update(assignee=None, assigned_timestamp=None)

    if assignee:
        objects = objects.filter(assignee__username=assignee)

    # It's essential that the objects are ordered for pagination. The
    # default ordering for flagged objects is by ascending created date.
    objects = paginate(request, objects)

    objects = set_form_action_for_objects(
        objects, reason=FlaggedObject.REASON_CONTENT_MODERATION, product_slug=product_slug
    )
    available_tags = SumoTag.objects.segmentation_tags().values("id", "name")

    for obj in objects:
        question = obj.content_object
        obj.available_topics = get_hierarchical_topics(question.product)
        obj.available_tags = available_tags
        obj.saved_tags = question.tags.values_list("id", flat=True)

    return render(
        request,
        "flagit/content_moderation.html",
        {
            "objects": objects,
            "locale": request.LANGUAGE_CODE,
            "products": [
                (p.slug, p.title)
                for p in Product.active.filter(codename="", aaq_configs__is_active=True)
            ],
            "selected_product": product_slug,
            "assignees": sorted(
                (user.username, user.get_full_name() or user.username)
                for user in User.objects.filter(
                    is_active=True,
                    groups__name="Content Moderators",
                ).distinct()
            ),
            "selected_assignee": assignee,
            "current_username": request.user.username,
        },
    )


@require_POST
@login_required
@permission_required("flagit.can_moderate")
def update(request, flagged_object_id):
    """Update the status of a flagged object."""
    flagged = get_object_or_404(FlaggedObject, pk=flagged_object_id)
    new_status = request.POST.get("status")
    reason = request.GET.get("reason")
    product = request.GET.get("product")
    ct = flagged.content_type

    if new_status:
        # If the object is an Answer let's fire a notification
        # if the flag is invalid
        if str(new_status) == str(FlaggedObject.FLAG_REJECTED) and ct.model_class() == Answer:
            answer = flagged.content_object
            QuestionReplyEvent(answer).fire(exclude=[answer.creator])

        flagged.status = new_status
        flagged.assignee = None
        flagged.assigned_timestamp = None
        flagged.save()
    if flagged.reason == FlaggedObject.REASON_CONTENT_MODERATION:
        question = flagged.content_object
        question.moderation_timestamp = timezone.now()
        question.save()
        if "hx-request" in request.headers:
            return HttpResponse(status=202)
        return HttpResponseRedirect(urlparams(reverse("flagit.moderate_content"), product=product))
    return HttpResponseRedirect(urlparams(reverse("flagit.flagged_queue"), reason=reason))
