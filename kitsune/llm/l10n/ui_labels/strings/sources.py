"""
The sources, and where each owner's files are inside them.

One source can hold the strings of several owners, and one owner's strings can be
spread over several sources.
"""

import re
from dataclasses import dataclass

LOCALE = r"(?P<strip>(?P<locale>[^/]+)/)"
ANDROID = r"/src/main/res/values(?P<strip>-(?P<locale>[^/]+))?/strings\.xml"
# Thunderbird for Android has Android and Compose resource folders. K-9 Mail's own
# strings are left out, and so are the names of test builds, which aren't under "main".
THUNDERBIRD_ANDROID = (
    r"(?!app-k9mail/).+/src/(?:main|androidMain|commonMain)/(?:res|composeResources)"
    r"/values(?P<strip>-(?P<locale>[^/]+))?/strings\.xml"
)
DESKTOP_FILES = r".+\.(?:ftl|properties|dtd)"
THUNDERBIRD_FILES = rf"(?!mail/branding/tb_beta/)(?:mail|chat|calendar)/{DESKTOP_FILES}"
# firefox-l10n also holds Firefox Enterprise's files. Firefox skips those. Enterprise
# skips Firefox's brand and the old copies of two of its own files.
ENTERPRISE_ONLY = r"browser/branding/enterprise/|(?:browser/browser|toolkit/toolkit)/enterprise/"
ENTERPRISE_SKIPPED = (
    r"browser/branding/official/|browser/browser/enterprise/(?:enterprise|felt)\.ftl"
)


@dataclass(frozen=True)
class OwnerFiles:
    """
    One owner's strings inside a repository.

    `files` matches the paths to read. Its `strip` group is the piece of a path that
    names the locale, and is left out of string IDs so they are the same in every
    locale. Its `locale` group is the product's code for the locale. A path with no
    code, or with the code in `english`, holds English.

    `app_name` is what a user sees where a string has a placeholder for the app's
    name, as in "About %1$s". Fluent files name the app themselves, so they need none.
    `measured_by` is for an owner with no list of shipped locales: the file whose
    share of translated strings decides whether a locale ships.
    `translates_every_locale` is False for an owner that also ships locales it has
    no translations for, and shows English there.
    """

    owner: str
    files: str
    english: str = ""
    app_name: str = ""
    measured_by: str = ""
    translates_every_locale: bool = True

    @property
    def translated(self) -> bool:
        return "locale" in re.compile(self.files).groupindex

    def match(self, path: str) -> tuple[str, str] | None:
        """Return the locale code ("" for English) and the path that goes in string IDs."""
        if not (match := re.fullmatch(self.files, path)):
            return None
        groups = match.groupdict()
        code = groups.get("locale") or ""
        if groups.get("strip"):
            start, end = match.span("strip")
            path = path[:start] + path[end:]
        return ("" if code == self.english else code), path


@dataclass(frozen=True)
class Source:
    """
    A repository of UI strings.

    `by_locale` says its top folders are locales, so each can be saved as soon as
    the download moves on to the next. Only the big repositories need that, and
    their English is in a repository of its own.
    """

    name: str
    repo: str
    owner_files: tuple[OwnerFiles, ...]
    ref: str = "main"
    by_locale: bool = False

    @property
    def owners(self) -> set[str]:
        return {owner_files.owner for owner_files in self.owner_files}


# An owner's brand names can sit in another repository than some of its strings.
# A source that provides them comes before the sources that need them, so that
# those are read again when the names change.
SOURCES = {
    source.name: source
    for source in (
        Source(
            "thunderbird-l10n-source",
            "thunderbird/thunderbird-l10n-source",
            (OwnerFiles("thunderbird", THUNDERBIRD_FILES, app_name="Thunderbird"),),
        ),
        Source(
            "thunderbird-l10n",
            "thunderbird/thunderbird-l10n",
            (OwnerFiles("thunderbird", rf"{LOCALE}{THUNDERBIRD_FILES}", app_name="Thunderbird"),),
            by_locale=True,
        ),
        Source(
            "enterprise-firefox-l10n",
            "mozilla-l10n/enterprise-firefox-l10n",
            (OwnerFiles("firefox-enterprise", rf"(?P<strip>en-US/){DESKTOP_FILES}"),),
        ),
        Source(
            "firefox-l10n-source",
            "mozilla-l10n/firefox-l10n-source",
            (
                OwnerFiles("firefox", rf"(?!_){DESKTOP_FILES}"),
                OwnerFiles(
                    "firefox-enterprise",
                    rf"(?!_|browser/branding/){DESKTOP_FILES}",
                ),
                OwnerFiles("thunderbird", rf"(?:toolkit|devtools)/{DESKTOP_FILES}"),
            ),
        ),
        Source(
            "firefox-l10n",
            "mozilla-l10n/firefox-l10n",
            (
                OwnerFiles("firefox", rf"{LOCALE}(?!{ENTERPRISE_ONLY}){DESKTOP_FILES}"),
                OwnerFiles(
                    "firefox-enterprise", rf"{LOCALE}(?!{ENTERPRISE_SKIPPED}){DESKTOP_FILES}"
                ),
                OwnerFiles("thunderbird", rf"{LOCALE}(?:toolkit|devtools)/{DESKTOP_FILES}"),
            ),
            by_locale=True,
        ),
        Source(
            "android-l10n",
            "mozilla-l10n/android-l10n",
            (
                OwnerFiles(
                    "firefox-android",
                    rf"mozilla-mobile/(?:fenix|android-components)/.+{ANDROID}",
                    app_name="Firefox",
                ),
                OwnerFiles(
                    "focus-android",
                    rf"mozilla-mobile/focus-android/.+{ANDROID}",
                    app_name="Firefox Focus",
                ),
            ),
        ),
        # The app's own repository has the translations that ship. Its new l10n
        # repository only keeps the English up to date so far.
        Source(
            "thunderbird-android",
            "thunderbird/thunderbird-android",
            (OwnerFiles("thunderbird-android", THUNDERBIRD_ANDROID, app_name="Thunderbird"),),
            ref="release",
        ),
        Source(
            "firefoxios-l10n",
            "mozilla-l10n/firefoxios-l10n",
            (
                OwnerFiles(
                    "firefox-ios",
                    rf"{LOCALE}firefox-ios\.xliff",
                    english="en-US",
                    app_name="Firefox",
                ),
            ),
        ),
        Source(
            "focusios-l10n",
            "mozilla-l10n/focusios-l10n",
            (
                OwnerFiles(
                    "focus-ios",
                    rf"{LOCALE}focus-ios\.xliff",
                    english="en-US",
                    app_name="Firefox Focus",
                ),
            ),
        ),
        Source(
            "mozilla-vpn-client-l10n",
            "mozilla-l10n/mozilla-vpn-client-l10n",
            (
                OwnerFiles(
                    "mozilla-vpn",
                    rf"{LOCALE}.+\.xliff",
                    english="en",
                    app_name="Mozilla VPN",
                    measured_by="mozillavpn.xliff",
                ),
            ),
        ),
        Source(
            "fxa-content-server-l10n",
            "mozilla/fxa-content-server-l10n",
            (OwnerFiles("mozilla-account", rf"locale/{LOCALE}[^/]+\.ftl", english="templates"),),
        ),
        Source(
            "sumo-l10n",
            "mozilla-l10n/sumo-l10n",
            # The site reads its Norwegian, Swedish and Sri Lankan Tamil from "no", "sv"
            # and "ta".
            (
                OwnerFiles(
                    "sumo",
                    rf"(?!nb_NO/|sv_SE/|ta_LK/){LOCALE}LC_MESSAGES/django(?:js)?\.pot?",
                    english="templates",
                    translates_every_locale=False,
                ),
            ),
            ref="master",
        ),
        Source(
            "addons-frontend-l10n",
            "mozilla-l10n/addons-frontend-l10n",
            (OwnerFiles("amo", rf"{LOCALE}LC_MESSAGES/amo\.pot?", english="templates"),),
        ),
    )
}
