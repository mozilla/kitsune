from functools import wraps

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404


def can_view_l10n_metrics(user):
    """Whether the user may view the L10n metrics dashboards.

    Access is granted to active users who either belong to one of the
    settings.L10N_METRICS_GROUPS groups, or are a leader, reviewer, or editor
    of any wiki Locale team. The two database-backed checks are combined into a
    single query.
    """
    if not (user.is_authenticated and user.is_active):
        return False

    return User.objects.filter(
        Q(groups__name__in=settings.L10N_METRICS_GROUPS)
        | Q(locales_leader__isnull=False)
        | Q(locales_reviewer__isnull=False)
        | Q(locales_editor__isnull=False),
        pk=user.pk,
    ).exists()


def l10n_metrics_access_required(view_func):
    """Restrict a view to users who can view the L10n metrics dashboards.

    Raises Http404 for everyone else, matching the behavior of group_required.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not can_view_l10n_metrics(request.user):
            raise Http404
        return view_func(request, *args, **kwargs)

    return _wrapped_view
