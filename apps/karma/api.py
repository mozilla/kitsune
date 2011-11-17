from access.decorators import login_required  # , permission_required
from karma.manager import KarmaManager
from sumo.decorators import render_to_json


@login_required
# TODO: setup permissions (how to do this without a model?)
#@permission_required('karma.admin')
@render_to_json
def users(request):
    """Returns list of user karma information.

    GET paramaters:
    * daterange - 7d, 1m, 3m, 6m or 1y (default: 1y)
    * sort - field to sort on (default: points). Order is always descending.
    * page - starts at 1 (default: 1)
    * pagesize - (default: 100)

    Returns list of objects with the following fields:
        userid, username, points, answer_count, answer_points,
        firstanswer_count, firstanswer_points, solution_count,
        solution_points, helpful_count, helpful_points,
        unhelpful_count, unhelpful_points
    """
    daterange = request.GET.get('daterange', '1y')
    sort = request.GET.get('sort', 'points')
    page = request.GET.get('page', 1)
    pagesize = request.GET.get('pagesize', 100)
    # TODO: add validation to all the fields. Maybe using django forms?

    mgr = KarmaManager()
    users = mgr.top_users(range=daterange, type=sort, count=pagesize,
                    offset=(page - 1) * pagesize)
    return {
        'users': [(u.id, u.username,
                   mgr.count(daterange=daterange)) for u in users],
        'user_schema': ['userid', 'username', 'points']}
