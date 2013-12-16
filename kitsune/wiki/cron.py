import cronjobs
import waffle

from kitsune.search.tasks import index_task
from kitsune.wiki import tasks
from kitsune.wiki.models import DocumentMappingType


@cronjobs.register
def rebuild_kb():
    # If rebuild on demand switch is on, do nothing.
    if waffle.switch_is_active('wiki-rebuild-on-demand'):
        return

    tasks.rebuild_kb()


@cronjobs.register
def reindex_kb():
    """Reindex wiki_document."""
    index_task.delay(DocumentMappingType, DocumentMappingType.get_indexable())
