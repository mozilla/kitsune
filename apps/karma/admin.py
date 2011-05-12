from django.contrib import admin
from django.shortcuts import render_to_response
from django.template import RequestContext

from karma.actions import KarmaManager
from questions.karma_actions import (AnswerAction, AnswerMarkedHelpfulAction,
                                     FirstAnswerAction, SolutionAction)


def karma(request):
    """Admin view that displays karma related data."""
    kmgr = KarmaManager()
    top_alltime = [_user_karma_alltime(u, kmgr) for u in kmgr.top_alltime()]
    top_week = [_user_karma_week(u, kmgr) for u in kmgr.top_week()]
    return render_to_response('karma/admin/karma.html',
                              {'title': 'Karma',
                               'top_alltime': top_alltime,
                               'top_week': top_week},
                              RequestContext(request, {}))

admin.site.register_view('karma', karma, 'Karma')


def _user_karma_alltime(user, kmgr):
    return {
        'user': user,
        'points': kmgr.total_points(user),
        'answers': kmgr.total_count(AnswerAction, user),
        'first_answers': kmgr.total_count(FirstAnswerAction, user),
        'helpful_votes': kmgr.total_count(AnswerMarkedHelpfulAction, user),
        'solutions': kmgr.total_count(SolutionAction, user),
    }


def _user_karma_week(user, kmgr):
    return {
        'user': user,
        'points': kmgr.week_points(user),
        'answers': kmgr.week_count(AnswerAction, user),
        'first_answers': kmgr.week_count(FirstAnswerAction, user),
        'helpful_votes': kmgr.week_count(AnswerMarkedHelpfulAction, user),
        'solutions': kmgr.week_count(SolutionAction, user),
    }
