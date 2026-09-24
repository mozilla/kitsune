from django.conf import settings
from django.core.checks import Warning, register


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
