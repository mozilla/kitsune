# Pruned and modified version of django-badger/badger/views.py
# https://github.com/mozilla/django-badger/blob/master/badger/views.py

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods

from kitsune.kbadge.models import Award, Badge
from kitsune.sumo.utils import paginate


def badges_list(request):
    """Badges list page"""
    qs = Badge.objects.order_by("-created")
    badges_page = paginate(request, qs, per_page=settings.BADGE_PAGE_SIZE)

    return render(
        request,
        "badger/badges_list.html",
        {
            "badges": badges_page
        },
    )


@require_http_methods(["HEAD", "GET"])
def detail(request, slug):
    """Badge detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_detail_by(request.user):
        return HttpResponseForbidden("Detail forbidden")

    awards = (Award.objects.filter(badge=badge).order_by("-created"))[: settings.BADGE_MAX_RECENT]

    return render(
        request,
        "badger/badge_detail.html",
        {
            "badge": badge,
            "award_list": awards,
        },
    )


def awards_list(request, slug=None):
    """Awards list page"""
    qs = Award.objects.order_by("-modified")

    badge = None
    if slug is not None:
        badge = get_object_or_404(Badge, slug=slug)
        qs = qs.filter(badge=badge)

    awards_page = paginate(request, qs, per_page=settings.BADGE_PAGE_SIZE)

    return render(
        request,
        "badger/awards_list.html",
        {
            "badge": badge,
            "awards": awards_page,
        },
    )


@require_GET
def award_detail(request, slug, id):
    """Award detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    award = get_object_or_404(Award, badge=badge, pk=id)

    if not award.allows_detail_by(request.user):
        return HttpResponseForbidden("Award detail forbidden")

    return render(
        request,
        "badger/award_detail.html",
        {
            "badge": badge,
            "award": award,
        },
    )


@require_GET
def awards_by_user(request, username):
    """Badge awards by user"""
    user = get_object_or_404(User, username=username)
    awards = Award.objects.filter(user=user)
    return render(
        request,
        "badger/awards_by_user.html",
        {
            "user": user,
            "award_list": awards,
        },
    )


@require_GET
def awards_by_badge(request, slug):
    """Badge awards by badge"""
    badge = get_object_or_404(Badge, slug=slug)
    awards = Award.objects.filter(badge=badge)
    return render(
        request,
        "badger/awards_by_badge.html",
        {
            "badge": badge,
            "awards": awards,
        },
    )


@require_GET
def badges_by_user(request, username):
    """Badges created by user"""
    user = get_object_or_404(User, username=username)
    badges = Badge.objects.filter(creator=user)
    return render(
        request,
        "badger/badges_by_user.html",
        {
            "user": user,
            "badge_list": badges,
        },
    )
