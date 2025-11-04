from celery import shared_task

from kitsune.community.utils import top_contributors_questions
from kitsune.karma.models import Title
from kitsune.sumo.decorators import skip_if_read_only_mode


@shared_task
@skip_if_read_only_mode
def update_top_contributors() -> None:
    top25_ids = [x["user"]["id"] for x in top_contributors_questions(count=25)[0]]
    Title.objects.set_top10_contributors(top25_ids[:10])
    Title.objects.set_top25_contributors(top25_ids[10:25])
