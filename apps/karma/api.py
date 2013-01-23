from datetime import datetime, date, timedelta

from access.decorators import login_required, permission_required
from karma.forms import (
    UserAPIForm, OverviewAPIForm, DetailAPIForm
)
from karma.manager import KarmaManager
from questions.models import Question, Answer
from sumo.decorators import json_view


@login_required
@permission_required('karma.view_dashboard')
@json_view
def users(request):
    """Returns list of user karma information.

    GET paramaters:
    * daterange - 7d, 1m, 3m, 6m or 1y (default: 1y)
    * sort - field to sort on (default: points). Order is always descending.
    * page - starts at 1 (default: 1)
    * pagesize - (default: 100)

    Returns list of objects with the following fields:
        userid, username, points, <action_types>
    """
    form = UserAPIForm(request.GET)
    if not form.is_valid():
        return {'success': False, 'errors': form.errors}

    daterange = form.cleaned_data.get('daterange') or '1y'
    sort = form.cleaned_data.get('sort') or 'points'
    page = form.cleaned_data.get('page') or 1
    pagesize = form.cleaned_data.get('pagesize') or 100

    mgr = KarmaManager()
    users = mgr.top_users(daterange, type=sort, count=pagesize,
                          offset=(page - 1) * pagesize) or []

    now = datetime.now()
    action_types = KarmaManager.action_types.keys()
    schema = ['id', 'username', 'lastactivity', 'points'] + action_types
    user_list = []
    for u in users:
        user = [u.id, u.username]
        last_activity = Answer.last_activity_for(u)
        user.append((now - last_activity).days if last_activity else None)
        user.append(mgr.count(daterange, u, type='points'))
        for t in action_types:
            user.append(mgr.count(daterange, u, type=t))
        user_list.append(user)

    return {
        'success': True,
        'results': user_list,
        'schema': schema}


@login_required
@permission_required('karma.view_dashboard')
@json_view
def overview(request):
    """Returns the overview for a daterange.

    GET paramaters:
    * daterange - 7d, 1m, 3m, 6m or 1y (default: 1y)

    Returns an overview dict with a count for all action types.
    """
    form = OverviewAPIForm(request.GET)
    if not form.is_valid():
        return {'success': False, 'errors': form.errors}

    daterange = form.cleaned_data.get('daterange') or '1y'

    mgr = KarmaManager()
    overview = {}
    for t in KarmaManager.action_types.keys():
        overview[t] = mgr.count(daterange, type=t)

    # TODO: Maybe have a karma action not assigned to a user for this?
    num_days = KarmaManager.date_ranges[daterange]
    start_day = date.today() - timedelta(days=num_days)
    overview['question'] = Question.objects.filter(
        created__gt=start_day).count()

    return {
        'success': True,
        'overview': overview}


@login_required
@permission_required('karma.view_dashboard')
@json_view
def details(request):
    """Returns monthly or daily totals for an action type.

    Feeds the dashboard chart.
    """
    mgr = KarmaManager()
    form = DetailAPIForm(request.GET)

    if not form.is_valid():
        return {'success': False, 'errors': form.errors}
    userid = form.cleaned_data.get('userid') or 'overview'
    daterange = form.cleaned_data.get('daterange') or '1y'
    counts = {}
    count_func = mgr.monthly_counts
    form.cleaned_data.pop('daterange')
    if daterange == '1w':
        count_func = mgr.daily_counts
    for t in KarmaManager.action_types.keys():
        counts[t], time_units = count_func(daterange, type=t, **form.cleaned_data)

    return {
        'success': True,
        'time_units': time_units,
        'counts': counts,
        'userid': userid
        }
