from django.utils.crypto import salted_hmac

from kitsune.users.models import Setting

THEME_PREFERENCES = ("system", "light", "dark")
DEFAULT_THEME_PREFERENCE = "system"

THEME_PREFERENCE_SETTING = "theme_preference"
THEME_OWNER_SALT = "kitsune.users.theme.owner"


def theme_preference_or_default(value) -> str:
    return value if value in THEME_PREFERENCES else DEFAULT_THEME_PREFERENCE


def get_theme_preference(user) -> str:
    """Unlike Setting.get_for_user, never creates a row."""
    if user.pk is None:
        return DEFAULT_THEME_PREFERENCE

    value = (
        Setting.objects.filter(user=user, name=THEME_PREFERENCE_SETTING)
        .values_list("value", flat=True)
        .first()
    )
    return theme_preference_or_default(value)


def set_theme_preference(user, preference) -> None:
    if user.pk is None:
        raise ValueError("A theme preference can only be stored for a saved user.")
    if preference not in THEME_PREFERENCES:
        raise ValueError(f"Unknown theme preference: {preference!r}")

    Setting.objects.update_or_create(
        user=user, name=THEME_PREFERENCE_SETTING, defaults={"value": preference}
    )


def theme_owner_key(user) -> str:
    """An opaque per-account key that lets a page detect that the session switched accounts."""
    if user.pk is None:
        raise ValueError("A theme owner key needs a saved user.")

    return salted_hmac(THEME_OWNER_SALT, str(user.pk), algorithm="sha256").hexdigest()
