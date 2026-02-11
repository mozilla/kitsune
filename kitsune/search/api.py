import json

from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from kitsune.access.decorators import group_required
from kitsune.search.es_utils import get_doc_types


@group_required("Staff")
@require_POST
@csrf_exempt
def reindex_document(request):
    """
    Force-reindex a specific document in Elasticsearch and refresh the index
    so it becomes immediately searchable.

    Testing-only endpoint, gated behind DEV + ENABLE_TESTING_ENDPOINTS.

    Expects JSON body:
        {
            "doc_type": "WikiDocument",  # required
            "obj_id": 12345              # required
        }
    """
    if not (settings.DEV and settings.ENABLE_TESTING_ENDPOINTS):
        raise Http404

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"message": "Invalid JSON payload."}, status=400)

    doc_type_name = data.get("doc_type")
    obj_id = data.get("obj_id")

    if not (doc_type_name and obj_id):
        return JsonResponse(
            {"message": 'Invalid JSON payload (missing "doc_type" or "obj_id").'},
            status=400,
        )

    # Validate doc_type is a known document type.
    valid_doc_types = {cls.__name__: cls for cls in get_doc_types()}
    doc_type = valid_doc_types.get(doc_type_name)
    if doc_type is None:
        return JsonResponse(
            {
                "message": f'Unknown doc_type "{doc_type_name}". '
                f"Valid types: {', '.join(sorted(valid_doc_types.keys()))}."
            },
            status=400,
        )

    # Look up the ORM object.
    model = doc_type.get_model()
    try:
        obj = model.objects.get(pk=obj_id)
    except model.DoesNotExist:
        return JsonResponse(
            {"message": f"{doc_type_name} with id {obj_id} does not exist."},
            status=404,
        )

    # Index the document synchronously with refresh=True so it's immediately searchable.
    if doc_type.update_document:
        doc_type.prepare(obj).to_action("update", doc_as_upsert=True, refresh=True)
    else:
        doc_type.prepare(obj).to_action("index", refresh=True)

    return JsonResponse(
        {"message": f"{doc_type_name} {obj_id} has been indexed and refreshed."}
    )
