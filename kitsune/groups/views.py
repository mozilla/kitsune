from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from kitsune.access.decorators import login_required
from kitsune.groups.forms import AddUserForm, GroupAvatarForm, GroupProfileForm
from kitsune.groups.models import GroupProfile
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import get_next_url, paginate
from kitsune.upload.tasks import create_image_thumbnail


def _remove_group_member(profile, user, request, remove_from_group=True):
    """
    Remove a member/leader from a group with validation.

    Handles both regular members and leaders, with appropriate validation
    and error messages for the last leader scenario.

    Args:
        profile: The GroupProfile to remove the user from
        user: The user to remove
        request: The HTTP request object
        remove_from_group: If True, removes user from group entirely.
                          If False, only removes from leaders (demotes to regular member).

    Returns True if removed successfully, False if validation failed.
    """
    is_leader = profile.leaders.filter(pk=user.pk).exists()

    if is_leader and not profile.can_remove_leader():
        msg = _(
            "Cannot remove {user} because they are the last leader of a root group. "
            "Root groups must always have at least one leader. "
            "Please assign another leader before removing this member."
        ).format(user=user.username)
        messages.add_message(request, messages.ERROR, msg)
        return False

    if is_leader:
        profile.leaders.remove(user)

    if remove_from_group:
        user.groups.remove(profile.group)

    return True


def list(request):
    """List all groups visible to the user."""
    groups = GroupProfile.objects.visible(request.user).select_related("group")

    for group in groups:
        group.has_children = group.numchild > 0
        parent = group.get_parent()
        group.parent_id = parent.id if parent else None

    return render(request, "groups/list.html", {"groups": groups})


def profile(request, group_slug, member_form=None, leader_form=None):
    prof = _get_group_profile_or_404(request.user, group_slug)
    leaders = prof.leaders.all().select_related("profile")
    members_qs = prof.group.user_set.all().select_related("profile")

    if not prof.can_view_inactive_members(request.user):
        leaders = leaders.filter(is_active=True)
        members_qs = members_qs.filter(is_active=True)

    members = paginate(request, members_qs, per_page=30)

    user_can_edit = prof.can_edit(request.user)
    user_can_moderate = prof.can_moderate_group(request.user)

    # Fetch hierarchy data in view for better performance
    parent = prof.get_parent()
    children = prof.get_visible_children(request.user)

    return render(
        request,
        "groups/profile.html",
        {
            "profile": prof,
            "leaders": leaders,
            "members": members,
            "user_can_edit": user_can_edit,
            "user_can_moderate": user_can_moderate,
            "member_form": member_form or AddUserForm(),
            "leader_form": leader_form or AddUserForm(),
            "parent": parent,
            "children": children,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, group_slug):
    prof = _get_group_profile_or_404(request.user, group_slug)

    if not prof.can_edit(request.user):
        raise PermissionDenied

    form = GroupProfileForm(request.POST or None, instance=prof)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.add_message(
            request, messages.SUCCESS, _("Group information updated successfully!")
        )
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, "groups/edit.html", {"form": form, "profile": prof})


@login_required
@require_http_methods(["GET", "POST"])
def edit_avatar(request, group_slug):
    """Edit group avatar."""
    prof = _get_group_profile_or_404(request.user, group_slug)

    if not prof.can_edit(request.user):
        raise PermissionDenied

    if request.method == "POST":
        form = GroupAvatarForm(request.POST, request.FILES, instance=prof, request=request)
    else:
        form = GroupAvatarForm(instance=prof, request=request)

    old_avatar_path = None

    if prof.avatar and default_storage.exists(prof.avatar.name):
        # Need to store the path, or else django's
        # form.is_valid() messes with it.
        old_avatar_path = prof.avatar.name

    if request.method == "POST" and form.is_valid():
        # Upload new avatar and replace old one.
        if old_avatar_path:
            default_storage.delete(old_avatar_path)

        content = create_image_thumbnail(form.instance.avatar.file, settings.AVATAR_SIZE)
        # We want everything as .png
        name = form.instance.avatar.name + ".png"
        prof.avatar.save(name, content, save=True)
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, "groups/edit_avatar.html", {"form": form, "profile": prof})


@login_required
@require_http_methods(["GET", "POST"])
def delete_avatar(request, group_slug):
    """Delete group avatar."""
    prof = _get_group_profile_or_404(request.user, group_slug)

    if not prof.can_edit(request.user):
        raise PermissionDenied

    if request.method == "POST":
        # Delete avatar here
        if prof.avatar:
            prof.avatar.delete()
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, "groups/confirm_avatar_delete.html", {"profile": prof})


@login_required
@require_POST
def add_member(request, group_slug):
    """Add a member to the group."""
    prof = _get_group_profile_or_404(request.user, group_slug)

    if not prof.can_edit(request.user):
        raise PermissionDenied

    form = AddUserForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data["users"]:
            user.groups.add(prof.group)
        msg = _("{users} added to the group successfully!").format(users=request.POST.get("users"))
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(prof.get_absolute_url())

    msg = _("There were errors adding members to the group, see below.")
    messages.add_message(request, messages.ERROR, msg)
    return profile(request, group_slug, member_form=form)


@login_required
@require_http_methods(["GET", "POST"])
def remove_member(request, group_slug, user_id):
    """Remove a member from the group."""
    prof = _get_group_profile_or_404(request.user, group_slug)
    user = get_object_or_404(User, id=user_id)

    if not prof.can_edit(request.user):
        raise PermissionDenied

    if request.method == "POST":
        if _remove_group_member(prof, user, request):
            msg = _("{user} removed from the group successfully!").format(user=user.username)
            messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, "groups/confirm_remove_member.html", {"profile": prof, "member": user})


@login_required
@require_POST
def add_leader(request, group_slug):
    """Add a leader to the group."""
    prof = _get_group_profile_or_404(request.user, group_slug)

    if not prof.can_moderate_group(request.user):
        raise PermissionDenied

    form = AddUserForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data["users"]:
            if not user.groups.filter(pk=prof.group.pk).exists():
                # If user isn't a member of group, add to members
                user.groups.add(prof.group)
            prof.leaders.add(user)
        msg = _("{users} added to the group leaders successfully!").format(
            users=request.POST.get("users")
        )
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(prof.get_absolute_url())

    msg = _("There were errors adding leaders to the group, see below.")
    messages.add_message(request, messages.ERROR, msg)
    return profile(request, group_slug, leader_form=form)


@login_required
@require_http_methods(["GET", "POST"])
def remove_leader(request, group_slug, user_id):
    """Remove a leader from the group."""
    prof = _get_group_profile_or_404(request.user, group_slug)
    user = get_object_or_404(User, id=user_id)

    if not prof.can_moderate_group(request.user):
        raise PermissionDenied

    if request.method == "POST":
        if _remove_group_member(prof, user, request, remove_from_group=False):
            msg = _("{user} removed from the group leaders successfully!").format(
                user=user.username
            )
            messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(prof.get_absolute_url())

    return render(request, "groups/confirm_remove_leader.html", {"profile": prof, "leader": user})


@login_required
@require_POST
def join_contributors(request):
    """Join the Contributors group."""
    next_url = get_next_url(request) or reverse("home")
    group = Group.objects.get(name="Contributors")
    request.user.groups.add(group)
    messages.add_message(
        request, messages.SUCCESS, _("You are now part of the Contributors group!")
    )
    return HttpResponseRedirect(next_url)


def _get_group_profile_or_404(user, slug):
    """Get the GroupProfile visible to the given user and identified by the given slug."""
    return get_object_or_404(GroupProfile.objects.visible(user), slug=slug)
