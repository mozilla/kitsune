import os

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

import jingo
from tower import ugettext as _

from access.decorators import login_required
from groups.forms import GroupProfileForm, GroupAvatarForm
from groups.models import GroupProfile
from upload.tasks import _create_image_thumbnail


def list(request):
    groups = GroupProfile.objects.select_related('group').all()
    return jingo.render(request, 'groups/list.html', {'groups': groups})


def profile(request, group_slug):
    prof = get_object_or_404(GroupProfile, slug=group_slug)
    leaders = prof.leaders.all()
    members = prof.group.user_set.all()
    user_can_edit = _user_can_edit(request.user, prof)
    return jingo.render(request, 'groups/profile.html',
                        {'profile': prof, 'leaders': leaders,
                         'members': members, 'user_can_edit': user_can_edit})


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

    return jingo.render(request, 'groups/edit.html',
                        {'form': form, 'profile': prof})


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

    return jingo.render(request, 'groups/edit_avatar.html',
                        {'form': form, 'profile': prof})


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

    return jingo.render(request, 'groups/confirm_avatar_delete.html',
                        {'profile': prof})


def _user_can_edit(user, group_profile):
    """Can the given user edit the given group profile?"""
    return (user.has_perm('groups.change_groupprofile') or
            user in group_profile.leaders.all())
