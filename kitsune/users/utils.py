import bisect
import logging
import random
from datetime import datetime, timedelta
from re import compile, escape
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext as _

from kitsune.flagit.handlers import FlagListener
from kitsune.forums.handlers import PostListener, ThreadListener
from kitsune.gallery.handlers import MediaListener
from kitsune.kbadge.handlers import AwardListener, BadgeListener
from kitsune.kbforums.handlers import PostListener as KBPostListener
from kitsune.kbforums.handlers import ThreadListener as KBThreadListener
from kitsune.messages.handlers import MessageListener
from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.questions.handlers import AAQListener
from kitsune.sumo import email_utils
from kitsune.tidings.models import Watch
from kitsune.users.handlers import UserDeletionPublisher
from kitsune.users.models import ContributionAreas, Deactivation, Setting
from kitsune.wiki.handlers import DocumentListener
from kitsune.wiki.utils import generate_short_url

log = logging.getLogger("k.users")


def get_community_team_member_info(email_type='contributor'):
    """Get a random member from the Community Team who has logged in within 7 days."""
    seven_days_ago = datetime.now() - timedelta(days=7)

    try:
        community_team = Group.objects.get(name="Community Team")
    except Group.DoesNotExist:
        community_team = None

    if community_team:
        active_members = community_team.user_set.filter(
            is_active=True,
            last_login__gte=seven_days_ago
        )

        if active_members.exists():
            member = random.choice(active_members)
            username = member.username

            # Build the PM URL
            campaign_map = {
                'contributor': 'new-contributor',
                'first_answer': 'first-answer',
                'first_l10n': 'first-revision'
            }
            campaign = campaign_map.get(email_type, 'new-contributor')

            pm_url = f"https://support.mozilla.org/en-US/messages/new?to={username}&utm_campaign={campaign}&utm_medium=bitly&utm_source=email"
            pm_link = generate_short_url(pm_url) or pm_url

            return {
                'username': username,
                'name': member.first_name or username,
                'pm_link': pm_link
            }

    # Default fallback - return generic Community Team info without PM link
    return {
        'username': 'Community Team',
        'name': 'Community Team',
        'pm_link': None
    }


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

    # Get Community Team member info for the email
    team_info = get_community_team_member_info()

    @email_utils.safe_translation
    def _make_mail(locale):
        context_vars = {"contributor": user}
        context_vars.update(team_info)

        mail = email_utils.make_mail(
            subject=_("Welcome to Mozilla Support Community! 🎉"),
            text_template="users/email/contributor.ltxt",
            html_template="users/email/contributor.html",
            context_vars=context_vars,
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

    username_regex = r"^{}[0-9]*$".format(escape(username))
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

        username = "{}{}".format(username, i + 1)

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


def delete_user_pipeline(user: User) -> None:
    """
    Deletes a user and all associated data.
    """

    publisher = UserDeletionPublisher(user=user)

    publisher.register_listener(ThreadListener())
    publisher.register_listener(PostListener())
    publisher.register_listener(KBThreadListener())
    publisher.register_listener(KBPostListener())
    publisher.register_listener(AAQListener())
    publisher.register_listener(DocumentListener())
    publisher.register_listener(MessageListener())
    publisher.register_listener(MediaListener())
    publisher.register_listener(AwardListener())
    publisher.register_listener(BadgeListener())
    publisher.register_listener(FlagListener())

    publisher.publish()
    user.delete()
