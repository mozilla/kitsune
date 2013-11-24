import os
from ast import literal_eval
from datetime import datetime

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.http import (HttpResponsePermanentRedirect, HttpResponseRedirect,
                         Http404, urlencode)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (require_http_methods, require_GET,
                                          require_POST)
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.http import base36_to_int

from django_browserid.auth import BrowserIDBackend
from django_browserid.base import get_audience
from django_browserid.forms import BrowserIDForm

from mobility.decorators import mobile_template
from session_csrf import anonymous_csrf
from statsd import statsd
from tidings.tasks import claim_watches
from tower import ugettext as _

from kitsune import users as constants
from kitsune.access.decorators import (
    logout_required, login_required, permission_required)
from kitsune.questions.models import (
    Question, user_num_answers, user_num_questions, user_num_solutions)
from kitsune.sumo import email_utils
from kitsune.sumo.decorators import ssl_required
from kitsune.sumo.helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import get_next_url, simple_paginate
from kitsune.upload.tasks import _create_image_thumbnail
from kitsune.users.forms import (
    ProfileForm, AvatarForm, EmailConfirmationForm, AuthenticationForm,
    EmailChangeForm, SetPasswordForm, PasswordChangeForm, SettingsForm,
    ForgotUsernameForm, RegisterForm, PasswordResetForm, BrowserIDSignupForm)
from kitsune.users.helpers import profile_url
from kitsune.users.models import (
    CONTRIBUTOR_GROUP, Group, Profile, RegistrationProfile, EmailChange,
    Deactivation)
from kitsune.users.utils import (
    handle_login, handle_register, try_send_email_with_form,
    add_to_contributors, suggest_username, deactivate_user)
from kitsune.wiki.models import (
    user_num_documents, user_documents, user_redirects)


@ssl_required
@anonymous_csrf
@require_http_methods(['GET', 'POST'])
def user_auth(request, contributor=False, register_form=None,
        login_form=None):
    """Try to log the user in, or register a user.

    POSTs from these forms do not come back to this view, but instead go to the
    login and register views, which may redirect back to this in case of error.
    """
    next_url = get_next_url(request) or reverse('home')

    if login_form is None:
        login_form = AuthenticationForm()
    if register_form is None:
        register_form = RegisterForm()

    return render(request, 'users/auth.html', {
        'login_form': login_form,
        'register_form': register_form,
        'contributor': contributor,
        'next_url': next_url})


@ssl_required
@anonymous_csrf
@mobile_template('users/{mobile/}login.html')
def login(request, template):
    """Try to log the user in."""
    if request.method == 'GET' and not request.MOBILE:
        url = reverse('users.auth') + '?' + request.GET.urlencode()
        return HttpResponsePermanentRedirect(url)

    next_url = get_next_url(request) or reverse('home')
    form = handle_login(request)

    if request.user.is_authenticated():
        # Add a parameter so we know the user just logged in.
        # fpa =  "first page authed" or something.
        next_url = urlparams(next_url, fpa=1)
        res = HttpResponseRedirect(next_url)
        max_age = (None if settings.SESSION_EXPIRE_AT_BROWSER_CLOSE
                        else settings.SESSION_COOKIE_AGE)
        res.set_cookie(settings.SESSION_EXISTS_COOKIE,
                       '1',
                       secure=False,
                       max_age=max_age)
        return res

    if request.MOBILE:
        return render(request, template, {
            'form': form,
            'next_url': next_url})

    return user_auth(request, login_form=form)


@ssl_required
@require_POST
def logout(request):
    """Log the user out."""
    auth.logout(request)
    statsd.incr('user.logout')

    res = HttpResponseRedirect(get_next_url(request) or reverse('home'))
    res.delete_cookie(settings.SESSION_EXISTS_COOKIE)
    return res


@ssl_required
@logout_required
@require_http_methods(['GET', 'POST'])
@anonymous_csrf
@mobile_template('users/{mobile/}')
def register(request, template, contributor=False):
    """Register a new user.

    :param contributor: If True, this is for registering a new contributor.

    """
    if request.method == 'GET' and not request.MOBILE:
        url = reverse('users.auth') + '?' + request.GET.urlencode()
        return HttpResponsePermanentRedirect(url)

    form = handle_register(request)
    if form.is_valid():
        return render(request, template + 'register_done.html')

    if request.MOBILE:
        return render(request, template + 'register.html', {
            'form': form})

    return user_auth(request, register_form=form)


def register_contributor(request):
    """Register a new user from the superheroes page."""
    return register(request, contributor=True)


@anonymous_csrf  # This view renders a login form
@mobile_template('users/{mobile/}activate.html')
def activate(request, template, activation_key, user_id=None):
    """Activate a User account."""
    activation_key = activation_key.lower()

    if user_id:
        user = get_object_or_404(User, id=user_id)
    else:
        user = RegistrationProfile.objects.get_user(activation_key)

    if user and user.is_active:
        messages.add_message(
            request, messages.INFO,
            _(u'Your account is already activated, log in below.'))
        return HttpResponseRedirect(reverse('users.login'))

    account = RegistrationProfile.objects.activate_user(activation_key,
                                                        request)
    my_questions = None
    form = AuthenticationForm()
    if account:
        # Claim anonymous watches belonging to this email
        statsd.incr('user.activate')
        claim_watches.delay(account)

        my_questions = Question.uncached.filter(creator=account)

        # Update created time to current time
        for q in my_questions:
            q.created = datetime.now()
            q.save(update=True)

    return render(request, template, {
        'account': account, 'questions': my_questions,
        'form': form})


@anonymous_csrf
@mobile_template('users/{mobile/}')
def resend_confirmation(request, template):
    """Resend confirmation email."""
    if request.method == 'POST':
        form = EmailConfirmationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                reg_prof = RegistrationProfile.objects.get(
                    user__email=email)
                if not reg_prof.user.is_active:
                    form = try_send_email_with_form(
                        RegistrationProfile.objects.send_confirmation_email,
                        form, 'email',
                        reg_prof)
                else:
                    form = try_send_email_with_form(
                        RegistrationProfile.objects.send_confirmation_email,
                        form, 'email',
                        reg_prof,
                        text_template='users/email/already_activated.ltxt',
                        html_template='users/email/already_activated.html',
                        subject=_('Account already activated'))
            except RegistrationProfile.DoesNotExist:
                # Send already active email if user exists
                try:
                    user = User.objects.get(email=email, is_active=True)

                    current_site = Site.objects.get_current()
                    email_kwargs = {'domain': current_site.domain,
                                    'login_url': reverse('users.login')}

                    subject = _('Account already activated')

                    @email_utils.safe_translation
                    def _make_mail(locale):
                        mail = email_utils.make_mail(
                            subject=subject,
                            text_template='users/email/already_activated.ltxt',
                            html_template='users/email/already_activated.html',
                            context_vars=email_kwargs,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to_email=user.email)

                        return mail

                    email_utils.send_messages(
                        [_make_mail(request.LANGUAGE_CODE)])
                except User.DoesNotExist:
                    # Don't leak existence of email addresses.
                    pass
            # Form may now be invalid if email failed to send.
            if form.is_valid():
                return render(
                    request, template + 'resend_confirmation_done.html',
                    {'email': email})
    else:
        form = EmailConfirmationForm()
    return render(request, template + 'resend_confirmation.html', {
        'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
@mobile_template('users/{mobile/}')
def change_email(request, template):
    """Change user's email. Send confirmation first."""
    if request.method == 'POST':
        form = EmailChangeForm(request.user, request.POST)
        u = request.user
        if form.is_valid() and u.email != form.cleaned_data['email']:
            # Delete old registration profiles.
            EmailChange.objects.filter(user=request.user).delete()
            # Create a new registration profile and send a confirmation email.
            email_change = EmailChange.objects.create_profile(
                user=request.user, email=form.cleaned_data['email'])
            EmailChange.objects.send_confirmation_email(
                email_change, form.cleaned_data['email'])
            return render(
                request, template + 'change_email_done.html',
                {'email': form.cleaned_data['email']})
    else:
        form = EmailChangeForm(request.user,
                               initial={'email': request.user.email})
    return render(request, template + 'change_email.html', {'form': form})


@require_GET
def confirm_change_email(request, activation_key):
    """Confirm the new email for the user."""
    activation_key = activation_key.lower()
    email_change = get_object_or_404(EmailChange,
                                     activation_key=activation_key)
    u = email_change.user
    old_email = u.email

    # Check that this new email isn't a duplicate in the system.
    new_email = email_change.email
    duplicate = User.objects.filter(email=new_email).exists()
    if not duplicate:
        # Update user's email.
        u.email = new_email
        u.save()

    # Delete the activation profile now, we don't need it anymore.
    email_change.delete()

    return render(request, 'users/change_email_complete.html', {
        'old_email': old_email, 'new_email': new_email,
        'username': u.username, 'duplicate': duplicate})


@require_GET
@mobile_template('users/{mobile/}profile.html')
def profile(request, template, user_id):
    user_profile = get_object_or_404(
        Profile, user__id=user_id)

    if not (request.user.has_perm('users.deactivate_users')
            or user_profile.user.is_active):
        raise Http404('No Profile matches the given query.')

    groups = user_profile.user.groups.all()
    return render(request, template, {
        'profile': user_profile,
        'groups': groups,
        'num_questions': user_num_questions(user_profile.user),
        'num_answers': user_num_answers(user_profile.user),
        'num_solutions': user_num_solutions(user_profile.user),
        'num_documents': user_num_documents(user_profile.user)})


@require_POST
@permission_required('users.deactivate_users')
def deactivate(request):
    user = get_object_or_404(User, id=request.POST['user_id'], is_active=True)
    deactivate_user(user, request.user)
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
def documents_contributed(request, user_id):
    user_profile = get_object_or_404(
        Profile, user__id=user_id, user__is_active=True)

    return render(request, 'users/documents_contributed.html', {
        'profile': user_profile,
        'documents': user_documents(user_profile.user),
        'redirects': user_redirects(user_profile.user)})


@login_required
@require_http_methods(['GET', 'POST'])
def edit_settings(request):
    """Edit user settings"""
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            form.save_for_user(request.user)
            messages.add_message(request, messages.INFO,
                                 _(u'Your settings have been saved.'))
            return HttpResponseRedirect(reverse('users.edit_settings'))
        # Invalid form
        return render(request, 'users/edit_settings.html', {
            'form': form})

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
    return render(request, 'users/edit_settings.html', {
        'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
@mobile_template('users/{mobile/}edit_profile.html')
def edit_profile(request, template):
    """Edit user profile."""
    try:
        user_profile = request.user.get_profile()
    except Profile.DoesNotExist:
        # TODO: Once we do user profile migrations, all users should have a
        # a profile. We can remove this fallback.
        user_profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            user_profile = form.save()
            new_timezone = user_profile.timezone
            if request.session.get('timezone', None) != new_timezone:
                request.session['timezone'] = new_timezone
            return HttpResponseRedirect(reverse('users.profile',
                                                args=[request.user.id]))
    else:  # request.method == 'GET'
        form = ProfileForm(instance=user_profile)

    # TODO: detect timezone automatically from client side, see
    # http://rocketscience.itteco.org/2010/03/13/automatic-users-timezone-determination-with-javascript-and-django-timezones/

    return render(request, template, {
        'form': form, 'profile': user_profile})


@login_required
@require_http_methods(['POST'])
def make_contributor(request):
    """Adds the logged in user to the contributor group"""
    group = Group.objects.get(name=CONTRIBUTOR_GROUP)
    request.user.groups.add(group)

    @email_utils.safe_translation
    def _make_mail(locale):
        mail = email_utils.make_mail(
            subject=_('Welcome to SUMO!'),
            text_template='users/email/contributor.ltxt',
            html_template='users/email/contributor.html',
            context_vars={'username': request.user.username},
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=request.user.email)

        return mail

    email_utils.send_messages([_make_mail(request.LANGUAGE_CODE)])

    if 'return_to' in request.POST:
        return HttpResponseRedirect(request.POST['return_to'])
    else:
        return HttpResponseRedirect(reverse('landings.get_involved'))


@login_required
@require_http_methods(['GET', 'POST'])
def edit_avatar(request):
    """Edit user avatar."""
    try:
        user_profile = request.user.get_profile()
    except Profile.DoesNotExist:
        # TODO: Once we do user profile migrations, all users should have a
        # a profile. We can remove this fallback.
        user_profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        # Upload new avatar and replace old one.
        old_avatar_path = None
        if user_profile.avatar and os.path.isfile(user_profile.avatar.path):
            # Need to store the path, not the file here, or else django's
            # form.is_valid() messes with it.
            old_avatar_path = user_profile.avatar.path
        form = AvatarForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            if old_avatar_path:
                os.unlink(old_avatar_path)
            user_profile = form.save()

            content = _create_image_thumbnail(user_profile.avatar.path,
                                              settings.AVATAR_SIZE, pad=True)
            # We want everything as .png
            name = user_profile.avatar.name + ".png"
            # Delete uploaded avatar and replace with thumbnail.
            user_profile.avatar.delete()
            user_profile.avatar.save(name, content, save=True)
            return HttpResponseRedirect(reverse('users.edit_profile'))

    else:  # request.method == 'GET'
        form = AvatarForm(instance=user_profile)

    return render(request, 'users/edit_avatar.html', {
        'form': form, 'profile': user_profile})


@login_required
@require_http_methods(['GET', 'POST'])
def delete_avatar(request):
    """Delete user avatar."""
    try:
        user_profile = request.user.get_profile()
    except Profile.DoesNotExist:
        # TODO: Once we do user profile migrations, all users should have a
        # a profile. We can remove this fallback.
        user_profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        # Delete avatar here
        if user_profile.avatar:
            user_profile.avatar.delete()
        return HttpResponseRedirect(reverse('users.edit_profile'))
    # else:  # request.method == 'GET'

    return render(request, 'users/confirm_avatar_delete.html', {
        'profile': user_profile})


@anonymous_csrf
@mobile_template('users/{mobile/}pw_reset_form.html')
def password_reset(request, template):
    """Password reset form.

    Based on django.contrib.auth.views. This view sends the email.

    """
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        was_valid = form.is_valid()
        if was_valid:
            # TODO: Since we're using Jingo in a way that doesn't
            # override the Django template loader, the pw_reset.ltxt
            # email template must be a Django template and not a Jinja
            # template.
            #
            # After we switch all the rendering everywhere, we can
            # probably change this back. Until then, I'm pretty sure
            # this won't get translated.
            try_send_email_with_form(
                form.save, form, 'email',
                use_https=request.is_secure(),
                token_generator=default_token_generator,
                text_template='users/email/pw_reset.ltxt',
                html_template='users/email/pw_reset.html',
                subject_template_name='users/email/pw_reset_subject.ltxt')
        # Form may now be invalid if email failed to send.
        # PasswordResetForm is invalid iff there is no user with the entered
        # email address.
        # The condition below ensures we don't leak existence of email address
        # _unless_ sending an email fails.
        if form.is_valid() or not was_valid:
            # Don't leak existence of email addresses.
            return HttpResponseRedirect(reverse('users.pw_reset_sent'))
    else:
        form = PasswordResetForm()

    return render(request, template, {'form': form})


@mobile_template('users/{mobile/}pw_reset_sent.html')
def password_reset_sent(request, template):
    """Password reset email sent.

    Based on django.contrib.auth.views. This view shows a success message after
    email is sent.

    """
    return render(request, template)


@ssl_required
@anonymous_csrf
@mobile_template('users/{mobile/}pw_reset_confirm.html')
def password_reset_confirm(request, template, uidb36=None, token=None):
    """View that checks the hash in a password reset link and presents a
    form for entering a new password.

    Based on django.contrib.auth.views.

    """
    try:
        uid_int = base36_to_int(uidb36)
    except ValueError:
        raise Http404

    user = get_object_or_404(User, id=uid_int)
    context = {}

    if default_token_generator.check_token(user, token):
        context['validlink'] = True
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('users.pw_reset_complete'))
        else:
            form = SetPasswordForm(None)
    else:
        context['validlink'] = False
        form = None
    context['form'] = form
    return render(request, template, context)


@mobile_template('users/{mobile/}pw_reset_complete.html')
def password_reset_complete(request, template):
    """Password reset complete.

    Based on django.contrib.auth.views. Show a success message.

    """
    form = AuthenticationForm()
    return render(request, template, {'form': form})


@login_required
@mobile_template('users/{mobile/}pw_change.html')
def password_change(request, template):
    """Change password form page."""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('users.pw_change_complete'))
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, template, {'form': form})


@login_required
@mobile_template('users/{mobile/}pw_change_complete.html')
def password_change_complete(request, template):
    """Change password complete page."""
    return render(request, template)


@anonymous_csrf
@mobile_template('users/{mobile/}forgot_username.html')
def forgot_username(request, template):
    """Forgot username form page.

    On POST, this view sends an email with the username.
    """
    if request.method == "POST":
        form = ForgotUsernameForm(request.POST)
        was_valid = form.is_valid()
        if was_valid:
            try_send_email_with_form(
                form.save, form, 'email',
                use_https=request.is_secure())

        # Form may now be invalid if email failed to send.
        # ForgotUsernameForm is invalid iff there is no user with the entered
        # email address.
        # The condition below ensures we don't leak existence of email address
        # _unless_ sending an email fails.
        if form.is_valid() or not was_valid:
            # Don't leak existence of email addresses.
            messages.add_message(
                request, messages.INFO,
                _(u"We've sent an email with the username to any account"
                   " using {email}.").format(email=form.data['email']))

            return HttpResponseRedirect(reverse('users.login'))
    else:
        form = ForgotUsernameForm()

    return render(request, template, {'form': form})


@csrf_exempt
@require_POST
@ssl_required
def browserid_verify(request):
    next = request.REQUEST.get('next')
    redirect_to = next or getattr(settings, 'LOGIN_REDIRECT_URL', '/')
    redirect_to_failure = getattr(settings, 'LOGIN_REDIRECT_URL_FAILURE', '/')

    form = BrowserIDForm(data=request.POST)

    if form.is_valid():
        verifier = BrowserIDBackend().get_verifier()
        result = verifier.verify(form.cleaned_data['assertion'], get_audience(request))
        if result:
            if request.user.is_authenticated() and request.user.email != result.email:
                # User is already signed and wants to change their email.
                request.user.email = result.email
                request.user.save()
                return redirect(reverse('users.edit_profile'))
            else:
                # Verified so log in
                email = result.email
                user = User.objects.filter(email=email)
                contributor = 'contributor' in request.POST

                if len(user) == 0:
                    # Add the email to the session and redirect to signup
                    request.session['browserid-email'] = email
                    signup_url = reverse('users.browserid_signup')
                    return redirect('%s?%s' % (signup_url,
                                               urlencode({'next': next})))
                else:
                    user = user[0]
                    user.backend = 'django_browserid.auth.BrowserIDBackend'

                    if contributor:
                        add_to_contributors(request, user)

                    auth.login(request, user)
                    return redirect(redirect_to)

    return redirect(redirect_to_failure)


@ssl_required
@anonymous_csrf
@mobile_template('users/{mobile/}browserid_signup.html')
def browserid_signup(request, template):
    next = request.REQUEST.get('next')
    redirect_to = next or getattr(settings, 'LOGIN_REDIRECT_URL', '/')
    redirect_to_failure = getattr(settings, 'LOGIN_REDIRECT_URL_FAILURE', '/')

    email = request.session.get('browserid-email', None)
    contributor = 'contributor' in request.POST

    if email:
        data = request.POST if request.method == 'POST' else None
        form = BrowserIDSignupForm(data)

        if form.is_valid():
            user = User.objects.create_user(form.cleaned_data['username'],
                                            email)
            user.save()

            # Create a new profile for the user
            Profile.objects.create(user=user, locale=request.LANGUAGE_CODE)

            # Check if the user should be added to the contributor group
            if contributor:
                add_to_contributors(request, user)

            # Log the user in
            user.backend = 'django_browserid.auth.BrowserIDBackend'
            auth.login(request, user)

            return redirect(redirect_to)
        else:
            form.fields['username'].initial = suggest_username(email)
            return render(request, template, {'persona_email': email,
                                              'next': next, 'form': form,
                                              'contributor': contributor})

    return redirect(redirect_to_failure)
