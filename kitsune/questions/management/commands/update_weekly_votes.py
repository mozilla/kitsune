from datetime import datetime
from datetime import timedelta

from django.core.management.base import BaseCommand

from kitsune.questions.models import Question
from kitsune.questions.models import QuestionVote
from kitsune.questions.tasks import update_question_vote_chunk
from kitsune.sumo.utils import chunked


class Command(BaseCommand):
    help = "Keep the num_votes_past_week value accurate."

    def handle(self, **options):
        # Get all questions (id) with a vote in the last week.
        recent = datetime.now() - timedelta(days=7)
        q = QuestionVote.objects.filter(created__gte=recent)
        q = q.values_list("question_id", flat=True).order_by("question")
        q = q.distinct()
        q_with_recent_votes = list(q)

        # Get all questions with num_votes_past_week > 0
        q = Question.objects.filter(num_votes_past_week__gt=0)
        q = q.values_list("id", flat=True)
        q_with_nonzero_votes = list(q)

        # Union.
        qs_to_update = list(set(q_with_recent_votes + q_with_nonzero_votes))

        # Chunk them for tasks.
        for chunk in chunked(qs_to_update, 50):
            update_question_vote_chunk.apply_async(args=[chunk])
