from access.decorators import login_required, permission_required
from karma.forms import UserAPIForm, OverviewAPIForm
from karma.manager import KarmaManager
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
    users = mgr.top_users(daterange=daterange, type=sort, count=pagesize,
                          offset=(page - 1) * pagesize) or []

    action_types = KarmaManager.action_types.keys()
    schema = ['id', 'username', 'points'] + action_types
    user_list = []
    for u in users:
        user = [u.id, u.username]
        user.append(mgr.count(u, daterange=daterange, type='points'))
        for t in action_types:
            user.append(mgr.count(u, daterange=daterange, type=t))
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
        overview[t] = mgr.count(daterange=daterange, type=t)

    return {
        'success': True,
        'overview': overview}


@login_required
@permission_required('karma.view_dashboard')
@json_view
def totals(request):
    """Returns (for now) monthly totals for each action type.

    Feeds the dashboard chart.
    """
    mgr = KarmaManager()

    # TODO: implement me

    return {
        'success': True}
