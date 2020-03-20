from ast import literal_eval
from uuid import uuid4

from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.views.decorators.http import (require_GET, require_http_methods,
                                          require_POST)
# from axes.decorators import watch_login
from mozilla_django_oidc.views import (OIDCAuthenticationRequestView,
                                       OIDCLogoutView)
from tidings.models import Watch

from kitsune import users as constants
from kitsune.access.decorators import (login_required, logout_required,
                                       permission_required)
from kitsune.kbadge.models import Award
from kitsune.questions.utils import (mark_content_as_spam, num_answers,
                                     num_questions, num_solutions)
from kitsune.sumo.decorators import ssl_required
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import get_next_url, simple_paginate
from kitsune.users.forms import ProfileForm, SettingsForm
from kitsune.users.models import Deactivation, Profile
from kitsune.users.templatetags.jinja_helpers import profile_url
from kitsune.users.utils import (add_to_contributors, deactivate_user,
                                 get_oidc_fxa_setting)
from kitsune.wiki.models import (user_documents, user_num_documents,
                                 user_redirects)


@ssl_required
@logout_required
@require_http_methods(['GET', 'POST'])
def user_auth(request, notification=None):
    """
    Show user authorization page which includes a link for
    FXA sign-up/login and the legacy login form
    """
    next_url = get_next_url(request) or reverse('home')

    return render(request, 'users/auth.html', {
        'next_url': next_url,
        'notification': notification
    })


@require_GET
def profile(request, username):
    # The browser replaces '+' in URL's with ' ' but since we never have ' ' in
    # URL's we can assume everytime we see ' ' it was a '+' that was replaced.
    # We do this to deal with legacy usernames that have a '+' in them.
    username = username.replace(' ', '+')

    user = User.objects.filter(username=username).first()

    if not user:
        try:
            user = get_object_or_404(User, id=username)
        except ValueError:
            raise Http404('No Profile matches the given query.')
        return redirect(reverse('users.profile', args=(user.username,)))

    user_profile = get_object_or_404(Profile, user__id=user.id)

    if not (request.user.has_perm('users.deactivate_users') or
            user_profile.user.is_active):
        raise Http404('No Profile matches the given query.')

    groups = user_profile.user.groups.all()
    return render(request, 'users/profile.html', {
        'profile': user_profile,
        'awards': Award.objects.filter(user=user_profile.user),
        'groups': groups,
        'num_questions': num_questions(user_profile.user),
        'num_answers': num_answers(user_profile.user),
        'num_solutions': num_solutions(user_profile.user),
        'num_documents': user_num_documents(user_profile.user)})


@login_required
@require_POST
def close_account(request):
    # Clear the profile
    user_id = request.user.id
    profile = get_object_or_404(Profile, user__id=user_id)
    profile.clear()
    profile.fxa_uid = '{user_id}-{uid}'.format(user_id=user_id, uid=str(uuid4()))
    profile.save()

    # Deactivate the user and change key information
    request.user.username = 'user%s' % user_id
    request.user.email = '%s@example.com' % user_id
    request.user.is_active = False

    # Remove from all groups
    request.user.groups.clear()

    request.user.save()

    # Log the user out
    auth.logout(request)

    return render(request, 'users/close_account.html')


@require_POST
@permission_required('users.deactivate_users')
def deactivate(request, mark_spam=False):
    user = get_object_or_404(User, id=request.POST['user_id'], is_active=True)
    deactivate_user(user, request.user)

    if mark_spam:
        mark_content_as_spam(user, request.user)

    return HttpResponseRedirect(profile_url(user))


@require_GET
@permission_required('users.deactivate_users')
def deactivation_log(request):
    deactivations_qs = Deactivation.objects.order_by('-date')
    deactivations = simple_paginate(request, deactivations_qs,
                                    per_page=constants.DEACTIVATIONS_PER_PAGE)
    return render(request, 'users/deactivation_log.html', {
        'deactivations': deactivations})


@require_GET
def documents_contributed(request, username):
    user_profile = get_object_or_404(
        Profile, user__username=username, user__is_active=True)

    return render(request, 'users/documents_contributed.html', {
        'profile': user_profile,
        'documents': user_documents(user_profile.user),
        'redirects': user_redirects(user_profile.user)})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_settings(request):
    """Edit user settings"""
    template = 'users/edit_settings.html'
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            form.save_for_user(request.user)
            messages.add_message(request, messages.INFO,
                                 _(u'Your settings have been saved.'))
            return HttpResponseRedirect(reverse('users.edit_settings'))
        # Invalid form
        return render(request, template, {'form': form})

    # Pass the current user's settings as the initial values.
    values = request.user.settings.values()
    initial = dict()
    for v in values:
        try:
            # Uses ast.literal_eval to convert 'False' => False etc.
            # TODO: Make more resilient.
            initial[v['name']] = literal_eval(v['value'])
        except (SyntaxError, ValueError):
            # Attempted to convert the string value to a Python value
            # but failed so leave it a string.
            initial[v['name']] = v['value']
    form = SettingsForm(initial=initial)
    return render(request, template, {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_watch_list(request):
    """Edit watch list"""
    watches = Watch.objects.filter(user=request.user).order_by('content_type')

    watch_list = []
    for w in watches:
        if w.content_object is not None:
            if w.content_type.name == 'question':
                # Only list questions that are not archived
                if not w.content_object.is_archived:
                    watch_list.append(w)
            else:
                watch_list.append(w)

    if request.method == 'POST':
        for w in watch_list:
            w.is_active = 'watch_%s' % w.id in request.POST
            w.save()

    return render(request, 'users/edit_watches.html', {
        'watch_list': watch_list})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_profile(request, username=None):
    """Edit user profile."""
    # If a username is specified, we are editing somebody else's profile.
    if username is not None and username != request.user.username:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404

        # Make sure the auth'd user has permission:
        if not request.user.has_perm('users.change_profile'):
            return HttpResponseForbidden()
    else:
        user = request.user

    try:
        user_profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        # TODO: Once we do user profile migrations, all users should have a
        # a profile. We can remove this fallback.
        user_profile = Profile.objects.create(user=user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            user_profile = form.save()
            new_timezone = user_profile.timezone
            tz_changed = request.session.get('timezone', None) != new_timezone
            if tz_changed and user == request.user:
                request.session['timezone'] = new_timezone
            return HttpResponseRedirect(reverse('users.profile',
                                                args=[user.username]))
    else:  # request.method == 'GET'
        form = ProfileForm(instance=user_profile)

    # TODO: detect timezone automatically from client side, see
    # http://rocketscience.itteco.org/2010/03/13/automatic-users-timezone-determination-with-javascript-and-django-timezones/  # noqa
    msgs = messages.get_messages(request)
    fxa_messages = [
        m.message for m in msgs if m.message.startswith('fxa_notification')
    ]
    if not fxa_messages and not user_profile.is_fxa_migrated:
        fxa_messages.append('fxa_notification_deprecation_warning')

    return render(request, 'users/edit_profile.html', {
        'form': form, 'profile': user_profile, 'fxa_messages': fxa_messages})


@login_required
@require_http_methods(['POST'])
def make_contributor(request):
    """Adds the logged in user to the contributor group"""
    add_to_contributors(request.user, request.LANGUAGE_CODE)

    if 'return_to' in request.POST:
        return HttpResponseRedirect(request.POST['return_to'])
    else:
        return HttpResponseRedirect(reverse('landings.get_involved'))


class FXAAuthenticateView(OIDCAuthenticationRequestView):

    @staticmethod
    def get_settings(attr, *args):
        """Override settings for Firefox Accounts.

        The default values for the OIDC lib are used for the SSO login in the admin
        interface. For Firefox Accounts we need to pass different values, pointing to the
        correct endpoints and RP specific attributes.
        """

        val = get_oidc_fxa_setting(attr)
        if val is not None:
            return val
        return super(FXAAuthenticateView, FXAAuthenticateView).get_settings(attr, *args)

    def get(self, request):
        is_contributor = request.GET.get('is_contributor') == 'True'
        request.session['is_contributor'] = is_contributor
        return super(FXAAuthenticateView, self).get(request)


class FXALogoutView(OIDCLogoutView):

    @staticmethod
    def get_settings(attr, *args):
        """Override the logout url for Firefox Accounts."""

        val = get_oidc_fxa_setting(attr)
        if val is not None:
            return val
        return super(FXALogoutView, FXALogoutView).get_settings(attr, *args)
