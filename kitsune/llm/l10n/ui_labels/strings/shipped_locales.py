"""
Which locales each owner ships.

A product's repository of translations holds more locales than the product ships,
and lists kept elsewhere about products don't match the releases. So each owner's
list is read from the file its own build or server reads. If that file were
wrong, the product would be wrong.
"""

import json
import re
from collections.abc import Callable, Collection

from django.conf import settings

from kitsune.llm.l10n.ui_labels.strings import github
from kitsune.llm.l10n.ui_labels.strings.locales import get_product_codes

FIREFOX = "mozilla-firefox/firefox"
FIREFOX_IOS = "mozilla-mobile/firefox-ios"


def first_words(text: str) -> list[str]:
    """Read Firefox's and Thunderbird's shipped-locales file: a code starts each line."""
    return [line.split()[0] for line in text.splitlines() if line.strip()]


def xcode_regions(text: str) -> list[str]:
    """Read the languages an iOS app is built for, from its Xcode project file."""
    regions = re.search(r"knownRegions = \((.*?)\);", text, re.DOTALL)
    return re.findall(r'[^\s,"]+', regions.group(1)) if regions else []


def javascript_langs(text: str) -> list[str]:
    """Read the `langs` list in the config file of the add-ons website."""
    langs = re.search(r"\blangs: \[(.*?)\]", text, re.DOTALL)
    return re.findall(r"'([^']+)'", langs.group(1)) if langs else []


def gradle_locale_filters(text: str) -> list[str]:
    """Read the languages an Android app is built with, from its Gradle build file."""
    filters = re.search(r"localeFilters \+= listOf\((.*?)\)", text, re.DOTALL)
    return re.findall(r'"([^"]+)"', filters.group(1)) if filters else []


# Where each owner's list is: (repository, branch, path, how to read the codes from the file).
# The two JSON files are a list of codes, and an object with a code for each key.
SHIPPED_LIST_FILES: dict[str, tuple[str, str, str, Callable[[str], list[str]]]] = {
    "firefox": (FIREFOX, "release", "browser/locales/shipped-locales", first_words),
    "thunderbird": (
        "thunderbird/thunderbird-desktop",
        "release",
        "mail/locales/shipped-locales",
        first_words,
    ),
    "firefox-enterprise": (
        "mozilla/enterprise-firefox",
        "enterprise-main",
        "browser/locales/enterprise-l10n-changesets.json",
        json.loads,
    ),
    "firefox-ios": (
        FIREFOX_IOS,
        "main",
        "firefox-ios/Client.xcodeproj/project.pbxproj",
        xcode_regions,
    ),
    "focus-ios": (
        FIREFOX_IOS,
        "main",
        "focus-ios/Blockzilla.xcodeproj/project.pbxproj",
        xcode_regions,
    ),
    "mozilla-account": (
        "mozilla/fxa",
        "main",
        "libs/shared/l10n/src/lib/supported-languages.json",
        json.loads,
    ),
    "amo": ("mozilla/addons-frontend", "master", "config/default.js", javascript_langs),
    "thunderbird-android": (
        "thunderbird/thunderbird-android",
        "release",
        "app-thunderbird/build.gradle.kts",
        gradle_locale_filters,
    ),
}

# Firefox's Android apps build their language list from the folders that hold a strings.xml.
ANDROID_APPS = {"firefox-android": "fenix", "focus-android": "focus-android"}
ANDROID_STRINGS = re.compile(r"values-([^/]+)/strings\.xml")


def get_shipped_codes(owner: str) -> set[str]:
    """
    Return the locale codes an owner ships, as the product spells them.

    Raise ValueError when the list names no SUMO locale: it's empty, or the file
    moved or changed shape. A caller must never fall back to every locale in the
    repository, because products ship fewer than that.
    """
    codes: Collection[str]
    if owner == "sumo":
        codes = set(settings.SUMO_LANGUAGES)
    elif owner in ANDROID_APPS:
        folder = f"mobile/android/{ANDROID_APPS[owner]}/app/src/main/res"
        codes = {
            match.group(1)
            for path in github.get_paths(FIREFOX, "release", folder)
            if (match := ANDROID_STRINGS.fullmatch(path))
        }
    else:
        repo, ref, path, read = SHIPPED_LIST_FILES[owner]
        codes = list(read(github.get_file_text(repo, ref, path)))
    if not all(isinstance(code, str) for code in codes) or not get_product_codes(codes):
        raise ValueError(f"Could not read the list of locales that {owner} ships.")
    return set(codes)
