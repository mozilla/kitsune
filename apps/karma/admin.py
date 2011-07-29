from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from karma.actions import KarmaAction
from karma.models import Title
from karma.tasks import init_karma, update_top_contributors
from questions.karma_actions import (AnswerAction, AnswerMarkedHelpfulAction,
                                     AnswerMarkedNotHelpfulAction,
                                     FirstAnswerAction, SolutionAction)


class TitleAdmin(admin.ModelAdmin):
    raw_id_fields = ('users', 'groups')

admin.site.register(Title, TitleAdmin)


# AdminPlus view:
def karma(request):
    """Admin view that displays karma related data."""
    if not request.user.has_perm('users.view_karma_points'):
        raise PermissionDenied

    if request.POST.get('init'):
        init_karma.delay()
        messages.add_message(request, messages.SUCCESS,
                             'init_karma task queued!')
        return HttpResponseRedirect(request.path)

    if request.POST.get('update-top'):
        update_top_contributors.delay()
        messages.add_message(request, messages.SUCCESS,
                             'update_top_contributors task queued!')
        return HttpResponseRedirect(request.path)

    kmgr = KarmaAction.objects
    top_alltime = [_user_karma_alltime(u, kmgr) for u in kmgr.top_alltime()]
    top_week = [_user_karma_week(u, kmgr) for u in kmgr.top_week()]

    username = request.GET.get('username')
    user_karma = None
    if username:
        try:
            user = User.objects.get(username=username)
            d = kmgr.user_data(user)
            user_karma = [{'key': k, 'value': d[k]} for k in sorted(d.keys())]
        except User.DoesNotExist:
            pass

    return render_to_response('karma/admin/karma.html',
                              {'title': 'Karma',
                               'top_alltime': top_alltime,
                               'top_week': top_week,
                               'username': username,
                               'user_karma': user_karma},
                              RequestContext(request, {}))

admin.site.register_view('karma', karma, 'Karma')


def _user_karma_alltime(user, kmgr):
    return {
        'user': user,
        'points': kmgr.total_points(user),
        'answers': kmgr.total_count(AnswerAction, user),
        'first_answers': kmgr.total_count(FirstAnswerAction, user),
        'helpful_votes': kmgr.total_count(AnswerMarkedHelpfulAction, user),
        'nothelpful_votes': kmgr.total_count(AnswerMarkedNotHelpfulAction,
                                             user),
        'solutions': kmgr.total_count(SolutionAction, user),
    }


def _user_karma_week(user, kmgr):
    return {
        'user': user,
        'points': kmgr.week_points(user),
        'answers': kmgr.week_count(AnswerAction, user),
        'first_answers': kmgr.week_count(FirstAnswerAction, user),
        'helpful_votes': kmgr.week_count(AnswerMarkedHelpfulAction, user),
        'nothelpful_votes': kmgr.week_count(AnswerMarkedNotHelpfulAction,
                                            user),
        'solutions': kmgr.week_count(SolutionAction, user),
    }
