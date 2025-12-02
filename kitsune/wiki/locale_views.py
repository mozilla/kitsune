from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from kitsune.access.decorators import login_required
from kitsune.groups.forms import AddUserForm
from kitsune.wiki.models import Locale
from kitsune.wiki.utils import active_contributors

LEADER = "leader"
REVIEWER = "reviewer"
EDITOR = "editor"
ROLE_ATTRS = {
    LEADER: "leaders",
    REVIEWER: "reviewers",
    EDITOR: "editors",
}


def locale_list(request):
    """List the support KB locales."""
    locales = Locale.objects.all()
    locale = request.LANGUAGE_CODE
    return render(request, "wiki/locale_list.html", {"locales": locales, "locale": locale})


def locale_details(request, locale_code, leader_form=None, reviewer_form=None, editor_form=None):
    """Show the locale details page."""
    locale = get_object_or_404(Locale, locale=locale_code)
    leaders = locale.leaders.all().select_related("profile")
    reviewers = locale.reviewers.all().select_related("profile")
    editors = locale.editors.all().select_related("profile")
    active = active_contributors(from_date=date.today() - timedelta(days=90), locale=locale_code)
    user_can_edit = _user_can_edit(request.user, locale)
    return render(
        request,
        "wiki/locale_details.html",
        {
            "locale": locale,
            "leaders": leaders,
            "reviewers": reviewers,
            "editors": editors,
            "active": active,
            "user_can_edit": user_can_edit,
            "leader_form": leader_form or AddUserForm(),
            "reviewer_form": reviewer_form or AddUserForm(),
            "editor_form": editor_form or AddUserForm(),
        },
    )


@login_required
@require_POST
def add_to_locale(request, locale_code, role):
    """Add a user to the locale role."""
    locale = get_object_or_404(Locale, locale=locale_code)

    if not _user_can_edit(request.user, locale):
        raise PermissionDenied

    form = AddUserForm(request.POST)
    if form.is_valid():
        for user in form.cleaned_data["users"]:
            getattr(locale, ROLE_ATTRS[role]).add(user)
        users_added = request.POST.get("users").replace(",", ", ")
        # Create a message about successfully added users, ensuring l10n
        match role:
            case "leader":
                # L10n: A message displayed after adding users to locale leaders (only accounts with corresponding permissions can do that!).
                # {users} is a list of usernames separated by commas, {locale} is a locale code.
                msg = _("{users} added to {locale} leaders successfully!").format(users=users_added, locale=locale)
            case "reviewer":
                # L10n: A message displayed after adding users to locale reviewers (only accounts with corresponding permissions can do that!).
                # {users} is a list of usernames separated by commas, {locale} is a locale code.
                msg = _("{users} added to {locale} reviewers successfully!").format(users=users_added, locale=locale)
            case "editor":
                # L10n: A message displayed after adding users to locale editors (only accounts with corresponding permissions can do that!).
                # {users} is a list of usernames separated by commas, {locale} is a locale code.
                msg = _("{users} added to {locale} editors successfully!").format(users=users_added, locale=locale)
            case _:
                # L10n: A message displayed after adding users to a locale role (only accounts with corresponding permissions can do that!).
                # {users} is a list of usernames separated by commas.
                msg = _("{users} added successfully!").format(users=users_added)
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    # L10n: A message displayed in case of errors when adding users to locale role (only accounts with corresponding permissions can do that!).
    msg = _("There were errors adding users, see below.")
    messages.add_message(request, messages.ERROR, msg)
    return locale_details(request, locale_code, **{role + "_form": form})


@login_required
@require_http_methods(["GET", "POST"])
def remove_from_locale(request, locale_code, user_id, role):
    """Remove a user from the locale role."""
    locale = get_object_or_404(Locale, locale=locale_code)
    user = get_object_or_404(User, id=user_id)

    if not _user_can_edit(request.user, locale):
        raise PermissionDenied

    if request.method == "POST":
        getattr(locale, ROLE_ATTRS[role]).remove(user)
        # Create a message about successfully removed users, ensuring l10n
        match role:
            case "leader":
                # L10n: A message displayed after removing a user from locale leaders (only accounts with corresponding permissions can do that!).
                # {user} is a username, {locale} is a locale code.
                msg = _("{user} removed from {locale} leaders successfully!").format(user=user.username, locale=locale)
            case "reviewer":
                # L10n: A message displayed after removing a user from locale reviewers (only accounts with corresponding permissions can do that!).
                # {user} is a username, {locale} is a locale code.
                msg = _("{user} removed from {locale} reviewers successfully!").format(user=user.username, locale=locale)
            case "editor":
                # L10n: A message displayed after removing a user from locale editors (only accounts with corresponding permissions can do that!).
                # {user} is a username, {locale} is a locale code.
                msg = _("{user} removed from {locale} editors successfully!").format(user=user.username, locale=locale)
            case _:
                # L10n: A message displayed after removing a user from a locale role (only accounts with corresponding permissions can do that!).
                # {user} is a username.
                msg = _("{user} removed successfully!").format(user=user.username)
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(locale.get_absolute_url())

    return render(
        request,
        "wiki/confirm_remove_from_locale.html",
        {"locale": locale, "leader": user, "role": role},
    )


def _user_can_edit(user, locale):
    """Can the given user edit the given locale members?"""
    return user.has_perm("wiki.change_locale") or user in locale.leaders.all()
