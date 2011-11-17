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
        userid, username, points, <action_types>
    """
    daterange = request.GET.get('daterange', '1y')
    sort = request.GET.get('sort', 'points')
    page = request.GET.get('page', 1)
    pagesize = request.GET.get('pagesize', 100)
    # TODO: add validation to all the fields. Maybe using django forms?

    mgr = KarmaManager()
    users = mgr.top_users(daterange=daterange, type=sort, count=pagesize,
                          offset=(page - 1) * pagesize)

    action_types = KarmaManager.action_types.keys()
    schema = ['userid', 'username', 'points'] + action_types
    user_list = []
    for u in users:
        user = [u.id, u.username]
        user.append(mgr.count(u, daterange=daterange, type='points'))
        for t in action_types:
            user.append(mgr.count(u, daterange=daterange, type=t))
        user_list.append(user)
    return {
        'users': user_list,
        'user_schema': schema}
