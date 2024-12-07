import json
from ast import literal_eval

import requests
import waffle
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.generic import View

# from axes.decorators import watch_login
from josepy.jwk import JWK
from josepy.jws import JWS
from mozilla_django_oidc.utils import import_from_settings

# from axes.decorators import watch_login
from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
    OIDCLogoutView,
)
from sentry_sdk import capture_exception, capture_message

from kitsune import users as constants
from kitsune.access.decorators import login_required, logout_required, permission_required
from kitsune.kbadge.models import Award
from kitsune.questions.utils import mark_content_as_spam, num_answers, num_questions, num_solutions
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import get_next_url, paginate, simple_paginate
from kitsune.tidings.models import Watch
from kitsune.users.forms import ContributionAreaForm, ProfileForm, SettingsForm, UserForm
from kitsune.users.models import SET_ID_PREFIX, AccountEvent, Deactivation, Profile
from kitsune.users.tasks import (
    process_event_delete_user,
    process_event_password_change,
    process_event_profile_change,
    process_event_subscription_state_change,
)
from kitsune.users.templatetags.jinja_helpers import profile_url
from kitsune.users.utils import (
    add_to_contributors,
    anonymize_user,
    deactivate_user,
    get_oidc_fxa_setting,
    user_is_bot,
)
from kitsune.wiki.models import user_documents, user_redirects


@logout_required
@require_http_methods(["GET", "POST"])
def user_auth(request, notification=None):
    """
    Show user authorization page which includes a link for
    FXA sign-up/login and the legacy login form
    """
    next_url = get_next_url(request) or reverse("home")
    return render(
        request,
        "users/auth.html",
        {"next_url": next_url, "notification": notification},
    )


def login(request):
    """
    This views is used as a wrapper for user_auth to login users
    with Mozilla accounts.
    """
    if request.method == "GET":
        url = reverse("users.auth") + "?" + request.GET.urlencode()
        return HttpResponsePermanentRedirect(url)

    if request.user.is_authenticated:
        # We re-direct to the profile screen
        user_profile_url = urlparams(
            reverse("users.profile", args=[request.user.username]),
            fpa=1,
        )
        return HttpResponseRedirect(user_profile_url)

    return user_auth(request)


@require_POST
def logout(request):
    """Log the user out.

    Simple compatibility wrapper that calls the OIDC logout for FxA.
    """
    return FXALogoutView.as_view()(request)


@require_GET
def profile(request, username):
    # The browser replaces '+' in URL's with ' ' but since we never have ' ' in
    # URL's we can assume everytime we see ' ' it was a '+' that was replaced.
    # We do this to deal with legacy usernames that have a '+' in them.

    username = username.replace(" ", "+")

    user = User.objects.filter(username=username).first()

    if not user:
        try:
            user = get_object_or_404(User, id=username)
        except ValueError:
            raise Http404("No Profile matches the given query.")
        return redirect(reverse("users.profile", args=(user.username,)))

    user_profile = get_object_or_404(Profile, user__id=user.id)

    if not (request.user.has_perm("users.deactivate_users") or user_profile.user.is_active):
        raise Http404("No Profile matches the given query.")

    groups = user_profile.user.groups.all()
    return render(
        request,
        "users/profile.html",
        {
            "profile": user_profile,
            "awards": Award.objects.filter(user=user_profile.user),
            "groups": groups,
            "num_questions": num_questions(user_profile.user),
            "num_answers": num_answers(user_profile.user),
            "num_solutions": num_solutions(user_profile.user),
            "num_documents": user_documents(user_profile.user, viewer=request.user).count(),
        },
    )


@login_required
@require_POST
def close_account(request):
    # Forbid this for bots.
    if user_is_bot(request.user):
        return HttpResponseForbidden()

    anonymize_user(request.user)

    # Log the user out
    auth.logout(request)

    return render(request, "users/close_account.html")


@require_POST
@permission_required("users.deactivate_users")
def deactivate(request, mark_spam=False):
    user = get_object_or_404(User, id=request.POST["user_id"], is_active=True)

    # Forbid this for bots.
    if user_is_bot(user):
        return HttpResponseForbidden()

    deactivate_user(user, request.user)

    if mark_spam:
        mark_content_as_spam(user, request.user)

    return HttpResponseRedirect(profile_url(user))


@require_GET
@permission_required("users.deactivate_users")
def deactivation_log(request):
    deactivations_qs = Deactivation.objects.order_by("-date")
    deactivations = simple_paginate(
        request, deactivations_qs, per_page=constants.DEACTIVATIONS_PER_PAGE
    )
    return render(request, "users/deactivation_log.html", {"deactivations": deactivations})


def questions_contributed(request, username):
    # plus sign (+) is converted to space
    username = username.replace(" ", "+")
    profile = get_object_or_404(Profile, user__username=username, user__is_active=True)

    questions = paginate(request, profile.user.questions.order_by("-created"))

    return render(
        request,
        "users/questions_contributed.html",
        {
            "profile": profile,
            "questions": questions,
        },
    )


def answers_contributed(request, username):
    # plus sign (+) is converted to space
    username = username.replace(" ", "+")
    profile = get_object_or_404(Profile, user__username=username, user__is_active=True)

    # don't paginate this, we have contributors with an incredible number of questions answered
    # which means the later pages would create queries taking > 10 seconds to run
    answers = profile.user.answers.order_by("-created").select_related("question")[:100]

    return render(
        request,
        "users/answers_contributed.html",
        {
            "profile": profile,
            "answers": answers,
        },
    )


@login_required
@require_GET
def subscribed_products(request, username):
    # plus sign (+) is converted to space
    username = username.replace(" ", "+")
    user = get_object_or_404(User, username=username, is_active=True)
    if user != request.user:
        raise Http404

    context = {"user": user, "products": user.profile.products.all()}
    return render(request, "users/user_subscriptions.html", context)


@require_GET
def documents_contributed(request, username):
    # plus sign (+) is converted to space
    username = username.replace(" ", "+")
    user_profile = get_object_or_404(Profile, user__username=username, user__is_active=True)

    return render(
        request,
        "users/documents_contributed.html",
        {
            "profile": user_profile,
            "documents": user_documents(user_profile.user, viewer=request.user),
            "redirects": user_redirects(user_profile.user, viewer=request.user),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit_settings(request):
    """Edit user settings"""
    # Forbid this for bots.
    if user_is_bot(request.user):
        return HttpResponseForbidden()

    template = "users/edit_settings.html"
    if request.method == "POST":
        settings_form = SettingsForm(request.POST)
        if settings_form.is_valid():
            settings_form.save_for_user(request.user)
            messages.add_message(request, messages.INFO, _("Your settings have been saved."))
            return HttpResponseRedirect(reverse("users.edit_settings"))
        # Invalid form
        return render(request, template, {"settings_form": settings_form})

    # Pass the current user's settings as the initial values.
    values = list(request.user.settings.values())
    initial = dict()
    for val in values:
        try:
            # Uses ast.literal_eval to convert 'False' => False etc.
            # TODO: Make more resilient.
            initial[val["name"]] = literal_eval(val["value"])
        except (SyntaxError, ValueError):
            # Attempted to convert the string value to a Python value
            # but failed so leave it a string.
            initial[val["name"]] = val["value"]
    settings_form = SettingsForm(initial=initial)
    return render(request, template, {"settings_form": settings_form})


@login_required
@require_http_methods(["GET", "POST"])
def edit_contribution_area(request):
    """Edit the user's contribution area."""
    # Forbid this for bots.
    if user_is_bot(request.user):
        return HttpResponseForbidden()

    template = "users/edit_contributions.html"
    contribution_form = ContributionAreaForm(request.POST or None, request=request)

    if contribution_form.is_valid():
        contribution_form.save()
        messages.add_message(request, messages.INFO, _("Your preferences have been saved."))
        return HttpResponseRedirect(reverse("users.edit_contribution_area"))
    return render(request, template, {"contribution_form": contribution_form})


@login_required
@require_http_methods(["GET", "POST"])
def edit_watch_list(request):
    """Edit watch list"""
    # Forbid this for bots.
    if user_is_bot(request.user):
        return HttpResponseForbidden()

    watches = Watch.objects.filter(user=request.user).order_by("content_type")

    watch_list = []
    for item in watches:
        if item.content_object is not None:
            if item.content_type.name == "question":
                # Only list questions that are not archived
                if not item.content_object.is_archived:
                    watch_list.append(item)
            else:
                watch_list.append(item)

    if request.method == "POST":
        for item in watch_list:
            item.is_active = "watch_%s" % item.id in request.POST
            item.save()

    return render(request, "users/edit_watches.html", {"watch_list": watch_list})


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile(request, username=None):
    """Edit user profile."""
    # If a username is specified, we are editing somebody else's profile.
    user = None
    if username:
        username = username.replace(" ", "+")

        if username != request.user.username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise Http404

            # Make sure the auth'd user has permission:
            if not request.user.has_perm("users.change_profile"):
                return HttpResponseForbidden()

    if not user:
        user = request.user

    try:
        user_profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        # TODO: Once we do user profile migrations, all users should have a
        # a profile. We can remove this fallback.
        user_profile = Profile.objects.create(user=user)

    # Forbid this for bots.
    if user_profile.is_bot:
        return HttpResponseForbidden()

    profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=user_profile)
    user_form = UserForm(request.POST or None, instance=user_profile.user)

    if profile_form.is_valid() and user_form.is_valid():
        user_profile = profile_form.save()
        user = user_form.save()
        new_timezone = user_profile.timezone
        if new_timezone:
            tz_changed = request.session.get("timezone", None) != new_timezone
            if tz_changed and user == request.user:
                request.session["timezone"] = new_timezone
        return HttpResponseRedirect(reverse("users.profile", args=[user.username]))

    # TODO: detect timezone automatically from client side, see
    msgs = messages.get_messages(request)
    fxa_messages = [m.message for m in msgs if m.message.startswith("fxa_notification")]

    return render(
        request,
        "users/edit_profile.html",
        {
            "profile_form": profile_form,
            "user_form": user_form,
            "profile": user_profile,
            "fxa_messages": fxa_messages,
        },
    )


@login_required
@require_http_methods(["POST"])
def make_contributor(request):
    """Adds the logged in user to the contributor group"""
    # Forbid this for bots.
    if user_is_bot(request.user):
        return HttpResponseForbidden()

    add_to_contributors(request.user, request.LANGUAGE_CODE)

    if "return_to" in request.POST:
        return HttpResponseRedirect(request.POST["return_to"])
    else:
        return HttpResponseRedirect(reverse("landings.contribute"))


def become(request, username=None):
    """
    Log in with only a username, for use in local development.
    Set ENABLE_DEV_LOGIN=True to enable.
    """
    if not (settings.DEV and settings.ENABLE_DEV_LOGIN):
        raise Http404

    user = User.objects.get(username=username)
    auth.login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    return HttpResponseRedirect(reverse("home"))


class FXAAuthenticateView(OIDCAuthenticationRequestView):
    @staticmethod
    def get_settings(attr, *args):
        """Override settings for Mozilla accounts.

        The default values for the OIDC lib are used for the SSO login in the admin
        interface. For Mozilla accounts we need to pass different values, pointing to the
        correct endpoints and RP specific attributes.
        """

        val = get_oidc_fxa_setting(attr)
        if val is not None:
            return val
        return super(FXAAuthenticateView, FXAAuthenticateView).get_settings(attr, *args)

    def get(self, request):
        if contribution_area := request.GET.get("contributor"):
            request.session["contributor"] = contribution_area

        request.session["login_locale"] = getattr(request, "LANGUAGE_CODE", settings.LANGUAGE_CODE)

        return super(FXAAuthenticateView, self).get(request)


class FXAAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    @staticmethod
    def get_settings(attr, *args):
        """Override settings for Mozilla accounts.

        The default values for the OIDC lib are used for the SSO login in the admin
        interface. For Mozilla accounts we need to pass different values, pointing to the
        correct endpoints and RP specific attributes.
        """

        val = get_oidc_fxa_setting(attr)
        if val is not None:
            return val
        return super(FXAAuthenticationCallbackView, FXAAuthenticationCallbackView).get_settings(
            attr, *args
        )

    def login_failure(self):
        messages.add_message(
            self.request,
            messages.ERROR,
            _(
                "This account is not active. "
                "Please contact an administrator if you believe this is an error"
            ),
        )
        if waffle.switch_is_active("log-login-failure"):
            # sentry will attempt to find an exception being handled
            # or if none is (I think by this point it will have been handled)
            # just send a stack trace
            capture_exception()
            # I might be completely wrong about the above so, for now, also send a message
            capture_message("This account is not active error.", level="error")

        return HttpResponseRedirect(reverse("home"))


class FXALogoutView(OIDCLogoutView):
    @staticmethod
    def get_settings(attr, *args):
        """Override the logout url for Mozilla accounts."""

        val = get_oidc_fxa_setting(attr)
        if val is not None:
            return val
        return super(FXALogoutView, FXALogoutView).get_settings(attr, *args)


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(View):
    """The flow here is based on the mozilla-django-oidc lib.

    If/When the said lib supports SET tokens this will be replaced by the lib.
    """

    @staticmethod
    def get_settings(attr, *args):
        """Override the logout url for Mozilla accounts."""

        val = get_oidc_fxa_setting(attr)
        if val is not None:
            return val
        return import_from_settings(attr, *args)

    def retrieve_matching_jwk(self, header):
        """Get the signing key by exploring the JWKS endpoint of the OP."""

        response_jwks = requests.get(
            self.get_settings("OIDC_OP_JWKS_ENDPOINT"),
            verify=self.get_settings("OIDC_VERIFY_SSL", True),
        )
        response_jwks.raise_for_status()
        jwks = response_jwks.json()

        key = None
        for jwk in jwks["keys"]:
            if jwk["kid"] != header.get("kid"):
                continue
            if "alg" in jwk and jwk["alg"] != header["alg"]:
                raise SuspiciousOperation("alg values do not match.")
            key = jwk
        if key is None:
            raise SuspiciousOperation("Could not find a valid JWKS.")
        return key

    def verify_token(self, token, **kwargs):
        """Validate the token signature."""

        token = force_bytes(token)
        jws = JWS.from_compact(token)
        header = json.loads(jws.signature.protected)

        try:
            header.get("alg")
        except KeyError:
            msg = "No alg value found in header"
            raise SuspiciousOperation(msg)

        jwk_json = self.retrieve_matching_jwk(header)
        jwk = JWK.from_json(jwk_json)

        if not jws.verify(jwk):
            msg = "JWS token verification failed."
            raise SuspiciousOperation(msg)

        # The 'token' will always be a byte string since it's
        # the result of base64.urlsafe_b64decode().
        # The payload is always the result of base64.urlsafe_b64decode().
        # In Python 3 and 2, that's always a byte string.
        # In Python3.6, the json.loads() function can accept a byte string
        # as it will automagically decode it to a unicode string before
        # deserializing https://bugs.python.org/issue17909
        return json.loads(jws.payload.decode("utf-8"))

    def process_events(self, payload):
        """Save the events in the db, and enqueue jobs to act upon them"""

        fxa_uid = payload.get("sub")
        events = payload.get("events")
        try:
            profile_obj = Profile.objects.get(fxa_uid=fxa_uid)
        except Profile.DoesNotExist:
            profile_obj = None

        for long_id, event in events.items():
            short_id = long_id.replace(SET_ID_PREFIX, "")

            account_event = AccountEvent.objects.create(
                issued_at=payload["iat"],
                jwt_id=payload["jti"],
                fxa_uid=fxa_uid,
                status=AccountEvent.UNPROCESSED if profile_obj else AccountEvent.IGNORED,
                body=json.dumps(event),
                event_type=short_id,
                profile=profile_obj,
            )

            if profile_obj:
                if short_id == AccountEvent.DELETE_USER:
                    process_event_delete_user.delay(account_event.id)
                elif short_id == AccountEvent.SUBSCRIPTION_STATE_CHANGE:
                    process_event_subscription_state_change.delay(account_event.id)
                elif short_id == AccountEvent.PASSWORD_CHANGE:
                    process_event_password_change.delay(account_event.id)
                elif short_id == AccountEvent.PROFILE_CHANGE:
                    process_event_profile_change.delay(account_event.id)
                else:
                    account_event.status = AccountEvent.NOT_IMPLEMENTED
                    account_event.save()

    def post(self, request, *args, **kwargs):
        authorization = request.META.get("HTTP_AUTHORIZATION")
        if not authorization:
            raise Http404

        auth = authorization.split()
        if auth[0].lower() != "bearer":
            raise Http404
        id_token = auth[1]

        payload = self.verify_token(id_token)

        if payload:
            issuer = payload["iss"]
            events = payload.get("events", "")
            fxa_uid = payload.get("sub", "")
            exp = payload.get("exp")

            # If the issuer is not Mozilla accounts raise a 404 error
            if settings.FXA_SET_ISSUER != issuer:
                raise Http404

            # If exp is in the token then it's an id_token that should not be here
            if any([not events, not fxa_uid, exp]):
                return HttpResponse(status=400)

            self.process_events(payload)

            return HttpResponse(status=202)
        raise Http404
