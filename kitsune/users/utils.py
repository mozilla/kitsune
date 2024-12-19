import bisect
import logging
from re import compile, escape
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext as _

from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.sumo import email_utils
from kitsune.tidings.models import Watch
from kitsune.users.models import ContributionAreas, Deactivation, Profile, Setting

log = logging.getLogger("k.users")


def add_to_contributors(user, language_code, contribution_area=""):
    area = contribution_area.upper()
    if not ContributionAreas.has_member(area):
        return

    group, created = Group.objects.get_or_create(name=ContributionAreas[area].value)
    # don't fire an email if the user is already member of the group
    if user.groups.filter(pk=group.pk).exists():
        return

    user.groups.add(group)
    user.save()

    @email_utils.safe_translation
    def _make_mail(locale):
        mail = email_utils.make_mail(
            subject=_("Welcome to SUMO!"),
            text_template="users/email/contributor.ltxt",
            html_template="users/email/contributor.html",
            context_vars={"contributor": user},
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=user.email,
        )

        return mail

    email_utils.send_messages([_make_mail(language_code)])


def normalize_username(username):
    """Removes any invalid characters from the username"""

    regex = compile(UnicodeUsernameValidator.regex)
    normalized_username = ""
    for char in username:
        if not regex.match(char):
            continue
        normalized_username += char
    return normalized_username


def suggest_username(email):
    username = normalize_username(email.split("@", 1)[0])

    username_regex = r"^{0}[0-9]*$".format(escape(username))
    users = User.objects.filter(username__iregex=username_regex)

    if users.count() > 0:
        ids = []
        for user in users:
            # get the number at the end
            i = user.username[len(username) :]

            # in case there's no number in the case where just the base is taken
            if i:
                i = int(i)
                bisect.insort(ids, i)
            else:
                ids.insert(0, 0)

        for index, i in enumerate(ids):
            if index + 1 < len(ids):
                suggested_number = i + 1
                # let's check if the number exists. Username can have leading zeroes
                # which translates to an array [0, 1, 1, 2]. Without the membership
                # check this snippet will return 2 which is wrong
                if suggested_number != ids[index + 1] and suggested_number not in ids:
                    break

        username = "{0}{1}".format(username, i + 1)

    return username


def deactivate_user(user, moderator):
    user.is_active = False
    user.save()
    # Clear user settings to remove incoming notifications
    Setting.objects.filter(user=user).delete()
    Watch.objects.filter(user=user).delete()

    deactivation = Deactivation(user=user, moderator=moderator)
    deactivation.save()


def anonymize_user(user):
    # Clear the profile
    uid = uuid4()
    profile = user.profile
    profile.clear()
    profile.fxa_uid = "{user_id}-{uid}".format(user_id=user.id, uid=str(uid))
    profile.save()

    # Change key information, clear the user's inbox/outbox, and deactivate the user.
    user.username = f"user{uid.int}"
    user.email = f"{uid.int}@example.com"
    # Delete the InboxMessage objects received and OutboxMessage objects sent by the
    # user. This does not affect the InboxMessage objects of the recipients of messages
    # sent by the user.
    InboxMessage.objects.filter(to=user).delete()
    OutboxMessage.objects.filter(sender=user).delete()
    deactivate_user(user, user)

    # Remove from all groups
    user.groups.clear()

    user.save()


def get_oidc_fxa_setting(attr):
    """Helper method to return the appropriate setting for Mozilla accounts authentication."""
    FXA_CONFIGURATION = {
        "OIDC_OP_TOKEN_ENDPOINT": settings.FXA_OP_TOKEN_ENDPOINT,
        "OIDC_OP_AUTHORIZATION_ENDPOINT": settings.FXA_OP_AUTHORIZATION_ENDPOINT,
        "OIDC_OP_USER_ENDPOINT": settings.FXA_OP_USER_ENDPOINT,
        "OIDC_OP_JWKS_ENDPOINT": settings.FXA_OP_JWKS_ENDPOINT,
        "OIDC_RP_CLIENT_ID": settings.FXA_RP_CLIENT_ID,
        "OIDC_RP_CLIENT_SECRET": settings.FXA_RP_CLIENT_SECRET,
        "OIDC_AUTHENTICATION_CALLBACK_URL": "users.fxa_authentication_callback",
        "OIDC_CREATE_USER": settings.FXA_CREATE_USER,
        "OIDC_RP_SIGN_ALGO": settings.FXA_RP_SIGN_ALGO,
        "OIDC_USE_NONCE": settings.FXA_USE_NONCE,
        "OIDC_RP_SCOPES": settings.FXA_RP_SCOPES,
        "LOGOUT_REDIRECT_URL": settings.FXA_LOGOUT_REDIRECT_URL,
        "OIDC_USERNAME_ALGO": settings.FXA_USERNAME_ALGO,
        "OIDC_STORE_ACCESS_TOKEN": settings.FXA_STORE_ACCESS_TOKEN,
        "OIDC_STORE_ID_TOKEN": settings.FXA_STORE_ID_TOKEN,
        "OIDC_AUTH_REQUEST_EXTRA_PARAMS": {
            "access_type": "offline",
        },
        "OIDC_ADD_TOKEN_INFO_TO_USER_CLAIMS": True,
        "OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS": settings.FXA_RENEW_ID_TOKEN_EXPIRY_SECONDS,
    }

    return FXA_CONFIGURATION.get(attr, None)


def user_is_contributor(user):
    """Return whether the user is a contributor."""
    return (
        user.is_authenticated
        and user.groups.filter(name__in=ContributionAreas.get_groups()).exists()
    )


def user_is_bot(user):
    """Return whether the user is a bot."""
    return Profile.objects.filter(user=user, is_bot=True).exists()
