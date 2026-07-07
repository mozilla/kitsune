from playwright_tests.messages.homepage_messages import HomepageMessages


class KBLocalePageMessages:
    """Messages and URLs for the KB /kb/locales list and per-locale team pages."""

    STAGE_HOMEPAGE = HomepageMessages.STAGE_HOMEPAGE_URL_EN_US
    LOCALES_LIST_URL = STAGE_HOMEPAGE + "kb/locales"
    LOCALES_LIST_HEADING = "Locales"
    TARGET_LOCALE = "de"
    LEADER = "leader"
    REVIEWER = "reviewer"
    EDITOR = "editor"

    @staticmethod
    def get_locale_details_url(locale_code: str) -> str:
        """The absolute URL of a locale team page (e.g. .../kb/locales/de/)."""
        return f"{KBLocalePageMessages.STAGE_HOMEPAGE}kb/locales/{locale_code}/"

    @staticmethod
    def get_locale_team_heading(locale_code: str) -> str:
        """The team page heading. en-US is the 'KB Team', all other locales are a
        'Localization Team' (see kitsune/wiki/jinja2/wiki/locale_details.html)."""
        if locale_code == "en-US":
            return f"[{locale_code}] KB Team"
        return f"[{locale_code}] Localization Team"

    @staticmethod
    def get_added_to_role_banner(users: str, locale_code: str, role: str) -> str:
        """Success banner shown after adding user(s) to a locale role."""
        return f"{users} added to {locale_code} {role}s successfully!"

    @staticmethod
    def get_removed_from_role_banner(user: str, locale_code: str, role: str) -> str:
        """Success banner shown after removing a user from a locale role."""
        return f"{user} removed from {locale_code} {role}s successfully!"
