from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_http_methods

from tower import ugettext as _

from access.decorators import login_required
from groups.forms import AddUserForm
from wiki.models import Locale


LEADER = 'leader'
REVIEWER = 'reviewer'
EDITOR = 'editor'
ROLE_ATTRS = {
    LEADER: 'leaders',
    REVIEWER: 'reviewers',
    EDITOR: 'editors',
}


def locale_list(request):
    """List the support KB locales."""
    locales = Locale.objects.all()
    return render(request, 'wiki/locale_list.html', {
        'locales': locales})


def locale_details(request, locale_code, leader_form=None, reviewer_form=None,
                   editor_form=None):
    """Show the locale details page."""
    locale = get_object_or_404(Locale, locale=locale_code)
    leaders = locale.leaders.all().select_related('profile')
    reviewers = locale.reviewers.all().select_related('profile')
    editors = locale.editors.all().select_related('profile')
    user_can_edit = _user_can_edit(request.user, locale)
    return render(
        request,
        'wiki/locale_details.html',
        {'locale': locale,
         'leaders': leaders,
         'reviewers': reviewers,
         'editors': editors,
         'user_can_edit': user_can_edit,
         'leader_form': leader_form or AddUserForm(),
         'reviewer_form': reviewer_form or AddUserForm(),
         'editor_form': editor_form or AddUserForm()})


@login_required
@require_POST
def add_to_locale(request, locale_code, role):
    """Add a user to the locale role."""
    locale = get_object_or_404(Locale, locale=locale_code)

    if not _user_can_edit(request.user, locale):
        raise PermissionDenied

    form = AddUserForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data['users']:
            getattr(locale, ROLE_ATTRS[role]).add(user)
        msg = _('{users} added successfully!').format(
            users=request.POST.get('users'))
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    msg = _('There were errors adding users, see below.')
    messages.add_message(request, messages.ERROR, msg)
    return locale_details(request, locale_code, **{role + '_form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def remove_from_locale(request, locale_code, user_id, role):
    """Remove a user from the locale role."""
    locale = get_object_or_404(Locale, locale=locale_code)
    user = get_object_or_404(User, id=user_id)

    if not _user_can_edit(request.user, locale):
        raise PermissionDenied

    if request.method == 'POST':
        getattr(locale, ROLE_ATTRS[role]).remove(user)
        msg = _('{user} removed from successfully!').format(
            user=user.username)
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    return render(request, 'wiki/confirm_remove_from_locale.html',
                        {'locale': locale, 'leader': user, 'role': role})


def _user_can_edit(user, locale):
    """Can the given user edit the given locale members?"""
    return (user.has_perm('wiki.change_locale') or
            user in locale.leaders.all())
