# Pruned and modified version of django-badger/badger/views.py
# https://github.com/mozilla/django-badger/blob/master/badger/views.py
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods
from django.views.generic.list import ListView

from kitsune.kbadge.models import Award
from kitsune.kbadge.models import Badge


class BadgesListView(ListView):
    """Badges list page"""

    model = Badge
    paginate_by = settings.BADGE_PAGE_SIZE
    template_name = "badger/badges_list.html"
    template_object_name = "badge"

    def get_queryset(self):
        qs = Badge.objects.order_by("-created")
        return qs


@require_http_methods(["HEAD", "GET"])
def detail(request, slug):
    """Badge detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_detail_by(request.user):
        return HttpResponseForbidden("Detail forbidden")

    awards = (Award.objects.filter(badge=badge).order_by("-created"))[: settings.BADGE_MAX_RECENT]

    return render(request, "badger/badge_detail.html", dict(badge=badge, award_list=awards,))


class AwardsListView(ListView):
    model = Award
    paginate_by = settings.BADGE_PAGE_SIZE
    template_name = "badger/awards_list.html"
    template_object_name = "award"

    def get_badge(self):
        if not hasattr(self, "badge"):
            self._badge = get_object_or_404(Badge, slug=self.kwargs.get("slug", None))
        return self._badge

    def get_queryset(self):
        qs = Award.objects.order_by("-modified")
        if self.kwargs.get("slug", None) is not None:
            qs = qs.filter(badge=self.get_badge())
        return qs

    def get_context_data(self, **kwargs):
        context = super(AwardsListView, self).get_context_data(**kwargs)
        if self.kwargs.get("slug", None) is None:
            context["badge"] = None
        else:
            context["badge"] = self.get_badge()
        return context


@require_GET
def award_detail(request, slug, id):
    """Award detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    award = get_object_or_404(Award, badge=badge, pk=id)

    if not award.allows_detail_by(request.user):
        return HttpResponseForbidden("Award detail forbidden")

    return render(request, "badger/award_detail.html", dict(badge=badge, award=award,))


@require_GET
def awards_by_user(request, username):
    """Badge awards by user"""
    user = get_object_or_404(User, username=username)
    awards = Award.objects.filter(user=user)
    return render(request, "badger/awards_by_user.html", dict(user=user, award_list=awards,))


@require_GET
def awards_by_badge(request, slug):
    """Badge awards by badge"""
    badge = get_object_or_404(Badge, slug=slug)
    awards = Award.objects.filter(badge=badge)
    return render(request, "badger/awards_by_badge.html", dict(badge=badge, awards=awards,))


@require_GET
def badges_by_user(request, username):
    """Badges created by user"""
    user = get_object_or_404(User, username=username)
    badges = Badge.objects.filter(creator=user)
    return render(request, "badger/badges_by_user.html", dict(user=user, badge_list=badges,))
