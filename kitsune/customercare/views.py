import json

from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.utils import generate_classification_tags
from kitsune.products.models import Topic


@require_POST
@permission_required("customercare.change_supportticket")
def update_topic(request, ticket_id):
    """Update topic for a support ticket."""
    ticket = get_object_or_404(SupportTicket, pk=ticket_id)

    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"error": "AJAX required"}, status=400)

    data = json.loads(request.body)
    new_topic_id = data.get("topic")

    try:
        new_topic = Topic.objects.get(id=new_topic_id, products=ticket.product)
    except Topic.DoesNotExist:
        return JsonResponse({"error": "Topic not found"}, status=404)

    ticket.topic = new_topic
    ticket.save(update_fields=["topic"])

    # Regenerate tags from new topic
    system_tags = [
        tag for tag in ticket.zendesk_tags if tag in ["loginless_ticket", "stage", "other"]
    ]
    classification_tags = generate_classification_tags(
        ticket, {"topic_result": {"topic": new_topic.title}}
    )
    ticket.zendesk_tags = system_tags + classification_tags
    ticket.save(update_fields=["zendesk_tags"])

    return JsonResponse({"updated_topic": str(new_topic)})
