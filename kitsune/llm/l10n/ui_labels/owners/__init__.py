"""
Owners: who they are, and which one each label of an article belongs to.

This file is the list of the owners we know about, each with a sentence that tells
an LLM what it is, and what we keep about one label's owner. `lookup.py` finds the
owner of each label of an article, by asking an LLM whose screen shows it.
`prompt.py` is what the LLM is told.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Owner:
    """
    An app or website with its own translated UI strings.

    `products` are the SUMO products whose articles are usually about it. The LLM
    is shown an owner's spots only for an article with one of these products.
    """

    name: str
    description: str
    products: tuple[str, ...]


UNKNOWN = "unknown"
CONFIG = "config"


@dataclass(frozen=True)
class LabelOwner:
    """
    What an LLM said about one label of an article: its owner, and its spot.

    `owner` is an owner's name, "unknown", or "config" for the name or value of a
    preference. `spot` is the IDs of the strings in the label's spot. It is empty
    when the LLM said none fits, and None when it was shown no spots for the owner.

    These fields are what `UILabelOwners` saves for a label. Raise `QUESTION_VERSION`
    when they change, so that answers saved with the old ones are asked for again.
    """

    kind: str
    text: str
    owner: str
    unknown_reason: str = ""
    spot: list[str] | None = None


# Why a label has no owner we know. A label's screen can belong to something else.
UNKNOWN_REASONS = {
    "os": "the operating system: Windows, macOS, a Linux desktop, Android or iOS system "
    "screens, system dialogs, file pickers, system settings, permission prompts",
    "website": "a website that isn't in the list, like Google, Microsoft, Flathub, Snapcraft "
    "or Thunderbird's add-ons site",
    "app": "another app: another browser, an antivirus program, an email app, an add-on's "
    "own pages, or a retired Mozilla product like Firefox OS, Lockwise or ScreenshotGo",
    "unclear": "you can't tell",
}

OWNERS = {
    owner.name: owner
    for owner in (
        Owner(
            "firefox",
            "Firefox desktop on Windows, macOS or Linux: menus, the toolbar, Settings, about: "
            "pages, the PDF viewer and the installer. Includes Firefox ESR and Firefox as "
            "companies deploy it.",
            ("firefox", "firefox-enterprise", "privacy-and-security"),
        ),
        Owner(
            "firefox-enterprise",
            "The Firefox Enterprise browser, Mozilla's separate enterprise build of Firefox. "
            "Not Firefox ESR, and not regular Firefox used at a company.",
            ("firefox-enterprise",),
        ),
        Owner(
            "firefox-android",
            "Firefox for Android, including Beta and ESR.",
            ("mobile", "firefox-preview", "firefox-android-esr"),
        ),
        Owner("firefox-ios", "Firefox for iPhone and iPad.", ("ios",)),
        Owner("focus-android", "Focus and Klar for Android.", ("focus-firefox", "klar")),
        Owner("focus-ios", "Focus and Klar for iPhone and iPad.", ("focus-firefox", "klar")),
        Owner(
            "thunderbird",
            "Thunderbird desktop, including its calendar and address book.",
            ("thunderbird",),
        ),
        Owner("thunderbird-android", "Thunderbird for Android.", ("thunderbird-android",)),
        Owner("mozilla-vpn", "The Mozilla VPN app on every platform.", ("mozilla-vpn",)),
        Owner(
            "mozilla-account",
            "Mozilla account web pages: sign-in, sign-up, account settings and connected devices.",
            ("mozilla-account",),
        ),
        Owner("relay", "The Relay website and add-on.", ("relay",)),
        Owner("monitor", "The Monitor website.", ("monitor",)),
        Owner("mdn-plus", "The MDN website.", ("mdn-plus",)),
        Owner(
            "amo",
            "addons.mozilla.org, the website for Firefox add-ons and themes. Not the Add-ons "
            "Manager inside Firefox (about:addons), which is firefox, and not Thunderbird's "
            "add-ons site.",
            ("firefox",),
        ),
        Owner(
            "sumo",
            "support.mozilla.org itself: its forums, Ask a Question, and the tools for editing "
            "and translating articles.",
            ("contributor",),
        ),
    )
}
