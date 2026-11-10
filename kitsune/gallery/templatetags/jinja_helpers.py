from django_jinja import library

from kitsune.gallery.utils import upload_knowledge_bases


@library.global_function
def media_knowledge_bases(user):
    """None means no picker filter; a user with private access but no knowledge bases gets []."""
    knowledge_bases = upload_knowledge_bases(user)
    if knowledge_bases is None:
        return None

    return [{"id": kb.pk, "name": kb.name} for kb in knowledge_bases]
