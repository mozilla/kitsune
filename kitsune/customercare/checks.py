import waffle
from django.conf import settings
from django.core.checks import Tags, Warning, register
from django.db import DatabaseError


@register()
def check_zendesk_oauth_configuration(app_configs, **kwargs):
    if bool(settings.ZENDESK_OAUTH_CLIENT_ID) != bool(settings.ZENDESK_OAUTH_CLIENT_SECRET):
        return [
            Warning(
                "Zendesk OAuth is only partially configured; legacy API token authentication "
                "will be used.",
                hint=(
                    "Set both ZENDESK_OAUTH_CLIENT_ID and ZENDESK_OAUTH_CLIENT_SECRET to enable "
                    "OAuth, or clear both to select legacy authentication explicitly."
                ),
                id="customercare.W001",
            )
        ]
    return []


@register()
def check_zendesk_chat_configuration(app_configs, **kwargs):
    configured = (
        settings.ZENDESK_CHAT_WIDGET_KEY,
        settings.ZENDESK_CHAT_SIGNING_SECRET,
        settings.ZENDESK_CHAT_SIGNING_KEY_ID,
    )
    if any(configured) and not all(configured):
        return [
            Warning(
                "Zendesk chat is only partially configured; chat will be unavailable.",
                hint=(
                    "Set ZENDESK_CHAT_WIDGET_KEY, ZENDESK_CHAT_SIGNING_SECRET, and "
                    "ZENDESK_CHAT_SIGNING_KEY_ID to enable chat, or clear all three."
                ),
                id="customercare.W002",
            )
        ]
    return []


@register(Tags.database)
def check_zendesk_chat_switch(app_configs, databases=None, **kwargs):
    if not databases or (
        settings.ZENDESK_CHAT_WIDGET_KEY
        or settings.ZENDESK_CHAT_SIGNING_SECRET
        or settings.ZENDESK_CHAT_SIGNING_KEY_ID
    ):
        return []
    try:
        # Read the row, not waffle's cache, so migrate never depends on Redis.
        switched_on = (
            waffle.get_waffle_switch_model()
            .objects.filter(name="zendesk-chat", active=True)
            .exists()
        )
    except DatabaseError:
        # On a fresh database, migrate runs checks before the switch table exists.
        return []
    if switched_on:
        return [
            Warning(
                "The zendesk-chat switch is active but Zendesk chat is not configured; chat "
                "will be unavailable.",
                hint=(
                    "Set ZENDESK_CHAT_WIDGET_KEY, ZENDESK_CHAT_SIGNING_SECRET, and "
                    "ZENDESK_CHAT_SIGNING_KEY_ID, or turn off the zendesk-chat switch."
                ),
                id="customercare.W003",
            )
        ]
    return []
