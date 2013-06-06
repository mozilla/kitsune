from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render

from kitsune.karma.manager import KarmaManager
from kitsune.karma.models import Title, Points
from kitsune.karma.tasks import (
    init_karma, update_top_contributors, recalculate_karma_points)
from kitsune.questions.karma_actions import (
    AnswerAction, AnswerMarkedHelpfulAction, AnswerMarkedNotHelpfulAction,
    FirstAnswerAction, SolutionAction)


class TitleAdmin(admin.ModelAdmin):
    raw_id_fields = ('users', 'groups')
    exclude = ('is_auto',)

    def queryset(self, request):
        qs = super(TitleAdmin, self).queryset(request)
        return qs.filter(is_auto=False)


admin.site.register(Title, TitleAdmin)


class PointsAdmin(admin.ModelAdmin):
    list_display = ('action', 'points', 'updated')
    readonly_fields = ('updated',)


admin.site.register(Points, PointsAdmin)


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

    if request.POST.get('recalculate'):
        recalculate_karma_points.delay()
        messages.add_message(request, messages.SUCCESS,
                             'recalculate_karma_points task queued!')
        return HttpResponseRedirect(request.path)

    if request.POST.get('update-top'):
        update_top_contributors.delay()
        messages.add_message(request, messages.SUCCESS,
                             'update_top_contributors task queued!')
        return HttpResponseRedirect(request.path)

    kmgr = KarmaManager()
    top_alltime = [_user_karma_alltime(u, kmgr) for
                   u in kmgr.top_users('all') or []]
    top_week = [_user_karma_week(u, kmgr) for
                u in kmgr.top_users(daterange='1w') or []]

    username = request.GET.get('username')
    user_karma = None
    if username:
        try:
            user = User.objects.get(username=username)
            d = kmgr.user_data(user)
            user_karma = [{'key': k, 'value': d[k]} for k in sorted(d.keys())]
        except User.DoesNotExist:
            pass

    return render(
        request,
        'admin/karma.html',
        {'title': 'Karma',
         'top_alltime': top_alltime,
         'top_week': top_week,
         'username': username,
         'user_karma': user_karma})

admin.site.register_view('karma', karma, 'Karma')


def _user_karma_alltime(user, kmgr):
    return {
        'user': user,
        'points': kmgr.count(user=user, type='points'),
        'answers': kmgr.count(user=user, type=AnswerAction.action_type),
        'first_answers': kmgr.count(
            user=user, type=FirstAnswerAction.action_type),
        'helpful_votes': kmgr.count(
            user=user, type=AnswerMarkedHelpfulAction.action_type),
        'nothelpful_votes': kmgr.count(
            user=user, type=AnswerMarkedNotHelpfulAction.action_type),
        'solutions': kmgr.count(user=user, type=SolutionAction.action_type),
    }


def _user_karma_week(user, kmgr):
    return {
        'user': user,
        'points': kmgr.count(daterange='1w', user=user, type='points'),
        'answers': kmgr.count(
            daterange='1w', user=user, type=AnswerAction.action_type),
        'first_answers': kmgr.count(
            daterange='1w', user=user, type=FirstAnswerAction.action_type),
        'helpful_votes': kmgr.count(
            daterange='1w', user=user, type=AnswerMarkedHelpfulAction.action_type),
        'nothelpful_votes': kmgr.count(
            daterange='1w', user=user,
            type=AnswerMarkedNotHelpfulAction.action_type),
        'solutions': kmgr.count(
            daterange='1w', user=user, type=SolutionAction.action_type),
    }
