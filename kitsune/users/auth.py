import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse as django_reverse
from django.db import transaction
from django.utils.translation import ugettext as _
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from kitsune.products.models import Product
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import Profile
from kitsune.users.utils import add_to_contributors, get_oidc_fxa_setting

log = logging.getLogger('k.users')


class SumoOIDCAuthBackend(OIDCAuthenticationBackend):

    def authenticate(self, request, **kwargs):
        """Authenticate a user based on the OIDC code flow."""

        # If the request has the /fxa/callback/ path then probably there is a login
        # with Firefox Accounts. In this case just return None and let
        # the FxA backend handle this request.
        if request and not request.path == django_reverse('oidc_authentication_callback'):
            return None

        return super(SumoOIDCAuthBackend, self).authenticate(request, **kwargs)


class FXAAuthBackend(OIDCAuthenticationBackend):

    @staticmethod
    def get_settings(attr, *args):
        """Override settings for Firefox Accounts Provider."""
        val = get_oidc_fxa_setting(attr)
        if val is not None:
            return val
        return super(FXAAuthBackend, FXAAuthBackend).get_settings(attr, *args)

    def create_user(self, claims):
        """Override create user method to mark the profile as migrated."""

        user = super(FXAAuthBackend, self).create_user(claims)
        # Create a user profile for the user and populate it with data from
        # Firefox Accounts
        profile = Profile.objects.get_or_create(user=user)[0]
        profile.is_fxa_migrated = True
        profile.fxa_uid = claims.get('uid')
        profile.fxa_avatar = claims.get('avatar', '')
        profile.name = claims.get('displayName', '')
        subscriptions = claims.get('subscriptions', [])
        # Let's get the first element even if it's an empty string
        # A few assertions return a locale of None so we need to default to empty string
        fxa_locale = (claims.get('locale', '') or '').split(',')[0]
        if fxa_locale in settings.SUMO_LANGUAGES:
            profile.locale = fxa_locale
        else:
            profile.locale = settings.LANGUAGE_CODE

        profile.save()
        # User subscription information
        products = Product.objects.filter(codename__in=subscriptions)
        profile.products.clear()
        profile.products.add(*products)

        # This is a new sumo profile, show edit profile message
        messages.success(
            self.request,
            _(
                '<strong>Welcome!</strong> You are now logged in using Firefox Accounts. ' +
                '{a_profile}Edit your profile.{a_close}<br>' +
                'Already have a different Mozilla Support Account? ' +
                '{a_more}Read more.{a_close}'
            ).format(
                a_profile='<a href="' + reverse('users.edit_my_profile') + '">',
                a_more='<a href="https://support.mozilla.org/en-US/kb/' +
                'firefox-accounts-mozilla-support-faq">',
                a_close='</a>'
            ),
            extra_tags="safe"
        )

        if self.request.session.get('is_contributor', False):
            add_to_contributors(user, self.request.LANGUAGE_CODE)
            del self.request.session['is_contributor']

        return user

    def filter_users_by_claims(self, claims):
        """Match users by FxA uid or email."""
        fxa_uid = claims.get('uid')
        user_model = get_user_model()
        users = user_model.objects.none()

        # something went terribly wrong. Return None
        if not fxa_uid:
            log.warning(u'Failed to get Firefox Account UID.')
            return users

        # A existing user is attempting to connect a Firefox Account to the SUMO profile
        # NOTE: this section will be dropped when the migration is complete
        if self.request and self.request.user and self.request.user.is_authenticated():
            return [self.request.user]

        users = user_model.objects.filter(profile__fxa_uid=fxa_uid)

        if not users:
            # We did not match any users so far. Let's call the super method
            # which will try to match users based on email
            users = super(FXAAuthBackend, self).filter_users_by_claims(claims)
        return users

    def get_userinfo(self, access_token, id_token, payload):
        """Return user details and subscription information dictionary."""

        user_info = super(FXAAuthBackend, self).get_userinfo(access_token, id_token, payload)

        if not settings.FXA_OP_SUBSCRIPTION_ENDPOINT:
            return user_info

        # Fetch subscription information
        try:
            sub_response = requests.get(
                settings.FXA_OP_SUBSCRIPTION_ENDPOINT,
                headers={
                    'Authorization': 'Bearer {0}'.format(access_token)
                },
                verify=self.get_settings('OIDC_VERIFY_SSL', True))
            sub_response.raise_for_status()
        except requests.exceptions.RequestException:
            log.error('Failed to fetch subscription status', exc_info=True)
            # if something went wrong, just return whatever the profile endpoint holds
            return user_info
        # This will override whatever the profile endpoint returns
        # until https://github.com/mozilla/fxa/issues/2463 is fixed
        user_info['subscriptions'] = sub_response.json().get('subscriptions', [])
        return user_info

    def update_user(self, user, claims):
        """Update existing user with new claims, if necessary save, and return user"""
        profile = user.profile
        fxa_uid = claims.get('uid')
        email = claims.get('email')
        user_attr_changed = False
        # Check if the user has active subscriptions
        subscriptions = claims.get('subscriptions', [])

        if not profile.is_fxa_migrated:
            # Check if there is already a Firefox Account with this ID
            if Profile.objects.filter(fxa_uid=fxa_uid).exists():
                msg = _('This Firefox Account is already used in another profile.')
                messages.error(self.request, msg)
                return None

            # If it's not migrated, we can assume that there isn't an FxA id too
            profile.is_fxa_migrated = True
            profile.fxa_uid = fxa_uid
            # This is the first time an existing user is using FxA. Redirect to profile edit
            # in case the user wants to update any settings.
            self.request.session['oidc_login_next'] = reverse('users.edit_my_profile')
            messages.info(self.request, 'fxa_notification_updated')

        # There is a change in the email in Firefox Accounts. Let's update user's email
        # unless we have a superuser
        if user.email != email and not user.is_staff:
            if User.objects.exclude(id=user.id).filter(email=email).exists():
                msg = _(u'The email used with this Firefox Account is already '
                        'linked in another profile.')
                messages.error(self.request, msg)
                return None
            user.email = email
            user_attr_changed = True

        # Follow avatars from FxA profiles
        profile.fxa_avatar = claims.get('avatar', '')
        # User subscription information
        products = Product.objects.filter(codename__in=subscriptions)
        profile.products.clear()
        profile.products.add(*products)

        # Users can select their own display name.
        if not profile.name:
            profile.name = claims.get('displayName', '')

        with transaction.atomic():
            if user_attr_changed:
                user.save()
            profile.save()
        return user

    def authenticate(self, request, **kwargs):
        """Authenticate a user based on the OIDC/oauth2 code flow."""

        # If the request has the /oidc/callback/ path then probably there is a login
        # attempt in the admin interface. In this case just return None and let
        # the OIDC backend handle this request.
        if request and request.path == django_reverse('oidc_authentication_callback'):
            return None

        return super(FXAAuthBackend, self).authenticate(request, **kwargs)
