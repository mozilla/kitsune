import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from tower import ugettext as _

from kitsune.access.decorators import login_required
from kitsune.groups.forms import (
    GroupProfileForm, GroupAvatarForm, AddUserForm)
from kitsune.groups.models import GroupProfile
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import get_next_url
from kitsune.upload.tasks import _create_image_thumbnail


def list(request):
    groups = GroupProfile.objects.select_related('group').all()
    return render(request, 'groups/list.html', {'groups': groups})


def profile(request, group_slug, member_form=None, leader_form=None):
    prof = get_object_or_404(GroupProfile, slug=group_slug)
    leaders = prof.leaders.all().select_related('profile')
    members_list = prof.group.user_set.all().select_related('profile')
    paginator = Paginator(members_list, 30)
    page = request.GET.get('page')
    try:
        members = paginator.page(page)
    except PageNotAnInteger:
        members = paginator.page(1)
    except EmptyPage:
        members = paginator.page(paginator.num_pages)

    is_paginated = paginator.num_pages > 1
    user_can_edit = _user_can_edit(request.user, prof)
    user_can_manage_leaders = _user_can_manage_leaders(request.user, prof)
    return render(request, 'groups/profile.html', {
        'profile': prof, 'leaders': leaders,
        'members': members, 'user_can_edit': user_can_edit,
        'user_can_manage_leaders': user_can_manage_leaders,
        'is_paginated': is_paginated,
        'member_form': member_form or AddUserForm(),
        'leader_form': leader_form or AddUserForm()})


@login_required
@require_http_methods(['GET', 'POST'])
def edit(request, group_slug):
    prof = get_object_or_404(GroupProfile, slug=group_slug)

    if not _user_can_edit(request.user, prof):
        raise PermissionDenied

    form = GroupProfileForm(request.POST or None, instance=prof)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.add_message(request, messages.SUCCESS,
                             _('Group information updated successfully!'))
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, 'groups/edit.html', {
        'form': form, 'profile': prof})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_avatar(request, group_slug):
    """Edit group avatar."""
    prof = get_object_or_404(GroupProfile, slug=group_slug)

    if not _user_can_edit(request.user, prof):
        raise PermissionDenied

    form = GroupAvatarForm(request.POST or None, request.FILES or None,
                           instance=prof)

    old_avatar_path = None
    if prof.avatar and os.path.isfile(prof.avatar.path):
        # Need to store the path, or else django's
        # form.is_valid() messes with it.
        old_avatar_path = prof.avatar.path
    if request.method == 'POST' and form.is_valid():
        # Upload new avatar and replace old one.
        if old_avatar_path:
            os.unlink(old_avatar_path)

        prof = form.save()
        content = _create_image_thumbnail(prof.avatar.path,
                                          settings.AVATAR_SIZE, pad=True)
        # We want everything as .png
        name = prof.avatar.name + ".png"
        # Delete uploaded avatar and replace with thumbnail.
        prof.avatar.delete()
        prof.avatar.save(name, content, save=True)
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, 'groups/edit_avatar.html', {
        'form': form, 'profile': prof})


@login_required
@require_http_methods(['GET', 'POST'])
def delete_avatar(request, group_slug):
    """Delete group avatar."""
    prof = get_object_or_404(GroupProfile, slug=group_slug)

    if not _user_can_edit(request.user, prof):
        raise PermissionDenied

    if request.method == 'POST':
        # Delete avatar here
        if prof.avatar:
            prof.avatar.delete()
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, 'groups/confirm_avatar_delete.html', {
        'profile': prof})


@login_required
@require_POST
def add_member(request, group_slug):
    """Add a member to the group."""
    prof = get_object_or_404(GroupProfile, slug=group_slug)

    if not _user_can_edit(request.user, prof):
        raise PermissionDenied

    form = AddUserForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data['users']:
            user.groups.add(prof.group)
        msg = _('{users} added to the group successfully!').format(
            users=request.POST.get('users'))
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(prof.get_absolute_url())

    msg = _('There were errors adding members to the group, see below.')
    messages.add_message(request, messages.ERROR, msg)
    return profile(request, group_slug, member_form=form)


@login_required
@require_http_methods(['GET', 'POST'])
def remove_member(request, group_slug, user_id):
    """Remove a member from the group."""
    prof = get_object_or_404(GroupProfile, slug=group_slug)
    user = get_object_or_404(User, id=user_id)

    if not _user_can_edit(request.user, prof):
        raise PermissionDenied

    if request.method == 'POST':
        if user in prof.leaders.all():
            # If user is a leader, remove from leaders
            prof.leaders.remove(user)
        user.groups.remove(prof.group)
        msg = (_('{user} removed from the group successfully!')
               .format(user=user.username))
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, 'groups/confirm_remove_member.html', {
        'profile': prof, 'member': user})


@login_required
@require_POST
def add_leader(request, group_slug):
    """Add a leader to the group."""
    prof = get_object_or_404(GroupProfile, slug=group_slug)

    if not _user_can_manage_leaders(request.user, prof):
        raise PermissionDenied

    form = AddUserForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data['users']:
            if prof.group not in user.groups.all():
                # If user isn't a member of group, add to members
                user.groups.add(prof.group)
            prof.leaders.add(user)
        msg = _('{users} added to the group leaders successfully!').format(
            users=request.POST.get('users'))
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(prof.get_absolute_url())

    msg = _('There were errors adding leaders to the group, see below.')
    messages.add_message(request, messages.ERROR, msg)
    return profile(request, group_slug, leader_form=form)


@login_required
@require_http_methods(['GET', 'POST'])
def remove_leader(request, group_slug, user_id):
    """Remove a leader from the group."""
    prof = get_object_or_404(GroupProfile, slug=group_slug)
    user = get_object_or_404(User, id=user_id)

    if not _user_can_manage_leaders(request.user, prof):
        raise PermissionDenied

    if request.method == 'POST':
        prof.leaders.remove(user)
        msg = (_('{user} removed from the group leaders successfully!')
               .format(user=user.username))
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, 'groups/confirm_remove_leader.html', {
        'profile': prof, 'leader': user})


@login_required
@require_POST
def join_contributors(request):
    """Join the Contributors group."""
    next = get_next_url(request) or reverse('home')
    group = Group.objects.get(name='Contributors')
    request.user.groups.add(group)
    messages.add_message(request, messages.SUCCESS,
                         _('You are now part of the Contributors group!'))
    return HttpResponseRedirect(next)


def _user_can_edit(user, group_profile):
    """Can the given user edit the given group profile?"""
    return (user.has_perm('groups.change_groupprofile') or
            user in group_profile.leaders.all())


def _user_can_manage_leaders(user, group_profile):
    """Can the given user add and remove leaders?"""
    # Limit to users with the change_groupprofile permission
    return user.has_perm('groups.change_groupprofile')
