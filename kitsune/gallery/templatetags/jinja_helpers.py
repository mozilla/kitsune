from django_jinja import library

from kitsune.gallery.utils import upload_knowledge_bases


@library.global_function
def media_knowledge_bases(user, private_audience_ids=None, all_knowledge_bases=False):
    """
    The private knowledge bases to list in the editor's image picker, or None for no list.

    An article in exactly one private knowledge base gets that one, since those are the
    only private images it can show. A new article has no knowledge bases until it is
    saved, so pass all_knowledge_bases=True to list every one the user may pick from.
    """
    one_private_kb = private_audience_ids is not None and len(private_audience_ids) == 1
    if not (all_knowledge_bases or one_private_kb):
        return None

    knowledge_bases = upload_knowledge_bases(user) or []
    if not all_knowledge_bases:
        knowledge_bases = [kb for kb in knowledge_bases if kb.pk in private_audience_ids]
    if not knowledge_bases:
        return None

    return [{"id": kb.pk, "name": kb.name} for kb in knowledge_bases]
