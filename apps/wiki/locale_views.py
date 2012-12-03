from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods

import jingo
from tower import ugettext as _

from access.decorators import login_required
from groups.forms import AddUserForm
from wiki.models import Locale


def locale_list(request):
    """List the support KB locales."""
    locales = Locale.objects.all()
    return jingo.render(request, 'wiki/locale_list.html',
                        {'locales': locales})


def locale_details(request, locale_code, leader_form=None, reviewer_form=None,
                   editor_form=None):
    """Show the locale details page."""
    locale = get_object_or_404(Locale, locale=locale_code)
    leaders = locale.leaders.all().select_related('profile')
    reviewers = locale.reviewers.all().select_related('profile')
    editors = locale.editors.all().select_related('profile')
    user_can_edit = _user_can_edit(request.user, locale)
    user_can_manage_leaders = _user_can_manage_leaders(request.user, locale)
    return jingo.render(
        request,
        'wiki/locale_details.html',
        {'locale': locale,
         'leaders': leaders,
         'reviewers': reviewers,
         'editors': editors,
         'user_can_edit': user_can_edit,
         'user_can_manage_leaders': user_can_manage_leaders,
         'leader_form': leader_form or AddUserForm(),
         'reviewer_form': reviewer_form or AddUserForm(),
         'editor_form': editor_form or AddUserForm()})


@login_required
@require_POST
def add_leader(request, locale_code):
    """Add a leader to the locale."""
    locale = get_object_or_404(Locale, locale=locale_code)

    if not _user_can_manage_leaders(request.user, locale):
        raise PermissionDenied

    form = AddUserForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data['users']:
            locale.leaders.add(user)
        msg = _('{users} added to the leaders successfully!').format(
            users=request.POST.get('users'))
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    msg = _('There were errors adding leaders, see below.')
    messages.add_message(request, messages.ERROR, msg)
    return locale_details(request, locale_code, leader_form=form)


@login_required
@require_http_methods(['GET', 'POST'])
def remove_leader(request, locale_code, user_id):
    """Remove a leader from the locale."""
    locale = get_object_or_404(Locale, locale=locale_code)
    user = get_object_or_404(User, id=user_id)

    if not _user_can_manage_leaders(request.user, locale):
        raise PermissionDenied

    if request.method == 'POST':
        locale.leaders.remove(user)
        msg = _('{user} removed from the leaders successfully!').format(
            user=user.username)
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    return jingo.render(request, 'wiki/confirm_remove_leader.html',
                        {'locale': locale, 'leader': user})


@login_required
@require_POST
def add_reviewer(request, locale_code):
    """Add a reviewer to the locale."""
    locale = get_object_or_404(Locale, locale=locale_code)

    if not _user_can_edit(request.user, locale):
        raise PermissionDenied

    form = AddUserForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data['users']:
            locale.reviewers.add(user)
        msg = _('{users} added to the reviewers successfully!').format(
            users=request.POST.get('users'))
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    msg = _('There were errors adding reviewers, see below.')
    messages.add_message(request, messages.ERROR, msg)
    return locale_details(request, locale_code, reviewer_form=form)


@login_required
@require_http_methods(['GET', 'POST'])
def remove_reviewer(request, locale_code, user_id):
    """Remove a reviewer from the locale."""
    locale = get_object_or_404(Locale, locale=locale_code)
    user = get_object_or_404(User, id=user_id)

    if not _user_can_edit(request.user, locale):
        raise PermissionDenied

    if request.method == 'POST':
        locale.reviewers.remove(user)
        msg = _('{user} removed from the reviewers successfully!').format(
            user=user.username)
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    return jingo.render(request, 'wiki/confirm_remove_reviewer.html',
                        {'locale': locale, 'reviewer': user})


@login_required
@require_POST
def add_editor(request, locale_code):
    """Add a editor to the locale."""
    locale = get_object_or_404(Locale, locale=locale_code)

    if not _user_can_edit(request.user, locale):
        raise PermissionDenied

    form = AddUserForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data['users']:
            locale.editors.add(user)
        msg = _('{users} added to the editors successfully!').format(
            users=request.POST.get('users'))
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    msg = _('There were errors adding editors, see below.')
    messages.add_message(request, messages.ERROR, msg)
    return locale_details(request, locale_code, editor_form=form)


@login_required
@require_http_methods(['GET', 'POST'])
def remove_editor(request, locale_code, user_id):
    """Remove a editor from the locale."""
    locale = get_object_or_404(Locale, locale=locale_code)
    user = get_object_or_404(User, id=user_id)

    if not _user_can_edit(request.user, locale):
        raise PermissionDenied

    if request.method == 'POST':
        locale.editors.remove(user)
        msg = _('{user} removed from the editors successfully!').format(
            user=user.username)
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    return jingo.render(request, 'wiki/confirm_remove_editor.html',
                        {'locale': locale, 'editor': user})


def _user_can_edit(user, locale):
    """Can the given user edit the given locale members?"""
    return (user.has_perm('wiki.change_locale') or
            user in locale.leaders.all())


def _user_can_manage_leaders(user, locale):
    """Can the given user add and remove locale leaders?"""
    # Limit to users with the change_groupprofile permission
    return user.has_perm('wiki.change_locale')
