import cronjobs

from kitsune.community.utils import top_contributors_questions
from kitsune.karma.models import Title


@cronjobs.register
def update_top_contributors():
    """"Update the top contributor lists and titles."""
    top25_ids = [x['user']['id'] for x in top_contributors_questions(count=25)[0]]
    Title.objects.set_top10_contributors(top25_ids[:10])
    Title.objects.set_top25_contributors(top25_ids[10:25])
