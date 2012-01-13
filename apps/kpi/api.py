from datetime import date, timedelta

from questions.models import Question
from sumo.decorators import json_view


@json_view
def percent_answered(request):
    start_day = date.today() - timedelta(days=180)
    qs = Question.objects.filter(
        created__gt=start_day)
    qs_without_solutions = qs.filter(solution__isnull=True)
    qs_with_solutions = qs.filter(solution__isnull=False)

    return {
        'data': {
            'without_solutions': qs_without_solutions.count(),
            'solutions': qs_with_solutions.count()
        },
        'success': True,
    }
