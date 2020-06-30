from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _lazy

# The number of answers per page.
ANSWERS_PER_PAGE = 20

# The number of questions per page.
QUESTIONS_PER_PAGE = 20

# Highest ranking to show for a user
HIGHEST_RANKING = 100

# Special tag names:
NEEDS_INFO_TAG_NAME = "needsinfo"
OFFTOPIC_TAG_NAME = "offtopic"

# How long until a question is automatically taken away from a user
TAKE_TIMEOUT = 600

# AAQ config:
products = OrderedDict(
    [
        (
            "desktop",
            {
                "name": _lazy("Firefox"),
                "subtitle": _lazy("Web browser for Windows, Mac and Linux"),
                "extra_fields": ["troubleshooting", "ff_version", "os", "plugins"],
                "tags": ["desktop"],
                "product": "firefox",
                "categories": OrderedDict(
                    [
                        # TODO: Just use the IA topics for this.
                        # See bug 979397
                        (
                            "download-and-install",
                            {
                                "name": _lazy("Download, install and migration"),
                                "topic": "download-and-install",
                                "tags": ["download-and-install"],
                            },
                        ),
                        (
                            "privacy-and-security",
                            {
                                "name": _lazy("Privacy and security settings"),
                                "topic": "privacy-and-security",
                                "tags": ["privacy-and-security"],
                            },
                        ),
                        (
                            "customize",
                            {
                                "name": _lazy("Customize controls, options and add-ons"),
                                "topic": "customize",
                                "tags": ["customize"],
                            },
                        ),
                        (
                            "fix-problems",
                            {
                                "name": _lazy(
                                    "Fix slowness, crashing, error messages and " "other problems"
                                ),
                                "topic": "fix-problems",
                                "tags": ["fix-problems"],
                            },
                        ),
                        (
                            "tips",
                            {"name": _lazy("Tips and tricks"), "topic": "tips", "tags": ["tips"],},
                        ),
                        (
                            "bookmarks",
                            {
                                "name": _lazy("Bookmarks"),
                                "topic": "bookmarks",
                                "tags": ["bookmarks"],
                            },
                        ),
                        (
                            "cookies",
                            {"name": _lazy("Cookies"), "topic": "cookies", "tags": ["cookies"],},
                        ),
                        ("tabs", {"name": _lazy("Tabs"), "topic": "tabs", "tags": ["tabs"],}),
                        (
                            "websites",
                            {
                                "name": _lazy("Websites"),
                                "topic": "websites",
                                "tags": ["websites"],
                            },
                        ),
                        (
                            "sync",
                            {"name": _lazy("Firefox Sync"), "topic": "sync", "tags": ["sync"],},
                        ),
                        ("other", {"name": _lazy("Other"), "topic": "other", "tags": ["other"],}),
                    ]
                ),
            },
        ),
        (
            "mobile",
            {
                "name": _lazy("Firefox for Android"),
                "subtitle": _lazy("Web browser for Android smartphones and tablets"),
                "extra_fields": ["ff_version", "os", "plugins"],
                "tags": ["mobile"],
                "product": "mobile",
                "categories": OrderedDict(
                    [
                        # TODO: Just use the IA topics for this.
                        # See bug 979397
                        (
                            "download-and-install",
                            {
                                "name": _lazy("Download, install and migration"),
                                "topic": "download-and-install",
                                "tags": ["download-and-install"],
                            },
                        ),
                        (
                            "privacy-and-security",
                            {
                                "name": _lazy("Privacy and security settings"),
                                "topic": "privacy-and-security",
                                "tags": ["privacy-and-security"],
                            },
                        ),
                        (
                            "customize",
                            {
                                "name": _lazy("Customize controls, options and add-ons"),
                                "topic": "customize",
                                "tags": ["customize"],
                            },
                        ),
                        (
                            "fix-problems",
                            {
                                "name": _lazy(
                                    "Fix slowness, crashing, error messages and " "other problems"
                                ),
                                "topic": "fix-problems",
                                "tags": ["fix-problems"],
                            },
                        ),
                        (
                            "tips",
                            {"name": _lazy("Tips and tricks"), "topic": "tips", "tags": ["tips"],},
                        ),
                        (
                            "bookmarks",
                            {
                                "name": _lazy("Bookmarks"),
                                "topic": "bookmarks",
                                "tags": ["bookmarks"],
                            },
                        ),
                        (
                            "cookies",
                            {"name": _lazy("Cookies"), "topic": "cookies", "tags": ["cookies"],},
                        ),
                        ("tabs", {"name": _lazy("Tabs"), "topic": "tabs", "tags": ["tabs"],}),
                        (
                            "websites",
                            {
                                "name": _lazy("Websites"),
                                "topic": "websites",
                                "tags": ["websites"],
                            },
                        ),
                        (
                            "sync",
                            {"name": _lazy("Firefox Sync"), "topic": "sync", "tags": ["sync"],},
                        ),
                        ("other", {"name": _lazy("Other"), "topic": "other", "tags": ["other"],}),
                    ]
                ),
            },
        ),
        (
            "ios",
            {
                "name": _lazy("Firefox for iOS"),
                "subtitle": _lazy("Firefox for iPhone, iPad and iPod touch devices"),
                "extra_fields": ["ff_version", "os", "plugins"],
                "tags": ["ios"],
                "product": "ios",
                "categories": OrderedDict(
                    [
                        (
                            "install-and-update-firefox-ios",
                            {
                                "name": _lazy("Install and Update"),
                                "topic": "install-and-update-firefox-ios",
                                "tags": ["install-and-update-firefox-ios"],
                            },
                        ),
                        (
                            "how-to-use-firefox-ios",
                            {
                                "name": _lazy("How to use Firefox for iOS"),
                                "topic": "how-to-use-firefox-ios",
                                "tags": ["how-to-use-firefox-ios"],
                            },
                        ),
                        (
                            "firefox-ios-not-working-expected",
                            {
                                "name": _lazy("Firefox for iOS is not working as expected"),
                                "topic": "firefox-ios-not-working-expected",
                                "tags": ["firefox-ios-not-working-expected"],
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "focus",
            {
                "name": _lazy("Firefox Focus"),
                "subtitle": _lazy("Automatic privacy browser and content blocker"),
                "extra_fields": [],
                "tags": ["focus-firefox"],
                "product": "focus-firefox",
                "categories": OrderedDict(
                    [
                        (
                            "Focus-ios",
                            {
                                "name": _lazy("Firefox Focus for iOS"),
                                "topic": "Focus-ios",
                                "tags": ["Focus-ios"],
                            },
                        ),
                        (
                            "firefox-focus-android",
                            {
                                "name": _lazy("Firefox Focus for Android"),
                                "topic": "firefox-focus-android",
                                "tags": ["firefox-focus-android"],
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "firefox-amazon-devices",
            {
                "name": _lazy("Firefox for Amazon Devices"),
                "subtitle": _lazy("Browser for Amazon devices"),
                "extra_fields": [],
                "tags": ["firefox-amazon"],
                "product": "firefox-amazon-devices",
                "categories": OrderedDict(
                    [
                        (
                            "firefox-fire-tv",
                            {
                                "name": _lazy("Firefox for Fire TV"),
                                "topic": "firefox-fire-tv",
                                "tags": ["firefox-fire-tv"],
                            },
                        ),
                        (
                            "firefox-echo-show",
                            {
                                "name": _lazy("Firefox for Echo Show"),
                                "topic": "firefox-echo-show",
                                "tags": ["firefox-echo-show"],
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "thunderbird",
            {
                "name": _lazy("Thunderbird"),
                "subtitle": _lazy("Email software for Windows, Mac and Linux"),
                "extra_fields": [],
                "tags": [],
                "product": "thunderbird",
                "categories": OrderedDict(
                    [
                        # TODO: Just use the IA topics for this.
                        # See bug 979397
                        (
                            "download-and-install",
                            {
                                "name": _lazy("Download, install and migration"),
                                "topic": "download-install-and-migration",
                                "tags": ["download-and-install"],
                            },
                        ),
                        (
                            "privacy-and-security",
                            {
                                "name": _lazy("Privacy and security settings"),
                                "topic": "privacy-and-security-settings",
                                "tags": ["privacy-and-security"],
                            },
                        ),
                        (
                            "customize",
                            {
                                "name": _lazy("Customize controls, options and add-ons"),
                                "topic": "customize-controls-options-and-add-ons",
                                "tags": ["customize"],
                            },
                        ),
                        (
                            "fix-problems",
                            {
                                "name": _lazy(
                                    "Fix slowness, crashing, error messages and " "other problems"
                                ),
                                "topic": "fix-slowness-crashing-error-messages-and-other-"
                                "problems",
                                "tags": ["fix-problems"],
                            },
                        ),
                        (
                            "calendar",
                            {
                                "name": _lazy("Calendar"),
                                "topic": "calendar",
                                "tags": ["calendar"],
                            },
                        ),
                        ("other", {"name": _lazy("Other"), "topic": "other", "tags": ["other"],}),
                    ]
                ),
            },
        ),
        (
            "firefox-lite",
            {
                "name": _lazy("Firefox Lite"),
                "subtitle": _lazy("Mobile browser for Indonesia"),
                "extra_fields": [],
                "tags": ["firefox-lite"],
                "product": "firefox-lite",
                "categories": OrderedDict(
                    [
                        (
                            "get-started",
                            {
                                "name": _lazy("Get started"),
                                "topic": "get-started",
                                "tags": ["get-started"],
                            },
                        ),
                        (
                            "fix-problems",
                            {
                                "name": _lazy("Fix problems"),
                                "topic": "fix-problems",
                                "tags": ["fix-problems"],
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "firefox-enterprise",
            {
                "name": _lazy("Firefox for Enterprise"),
                "subtitle": _lazy("Enterprise version of Firefox"),
                "extra_fields": [],
                "tags": [],
                "product": "firefox-enterprise",
                "categories": OrderedDict(
                    [
                        (
                            "deploy-firefox-for-enterprise",
                            {
                                "name": _lazy("Deploy"),
                                "topic": "deploy-firefox-for-enterprise",
                                "tags": ["deployment"],
                            },
                        ),
                        (
                            "policies-customization-enterprise",
                            {
                                "name": _lazy("Manage updates, policies & customization"),
                                "topic": "policies-customization-enterprise",
                                "tags": ["customization"],
                            },
                        ),
                        (
                            "manage-add-ons-enterprise",
                            {
                                "name": _lazy("Manage add-ons"),
                                "topic": "manage-add-ons-enterprise",
                                "tags": ["customization"],
                            },
                        ),
                        (
                            "manage-certificates-firefox-enterprise",
                            {
                                "name": _lazy("Manage certificates"),
                                "topic": "manage-certificates-firefox-enterprise",
                                "tags": ["customization"],
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "firefox-reality",
            {
                "name": _lazy("Firefox Reality"),
                "subtitle": _lazy("Firefox for Virtual Reality"),
                "extra_fields": [],
                "tags": [],
                "product": "firefox-reality",
                "categories": OrderedDict(
                    [
                        (
                            "get-started",
                            {
                                "name": _lazy("Get started with Firefox Reality"),
                                "topic": "get-started",
                                "tags": ["get-started"],
                            },
                        ),
                        (
                            "troubleshooting-reality",
                            {
                                "name": _lazy("Troubleshooting Firefox Reality"),
                                "topic": "troubleshooting-reality",
                                "tags": ["troubleshooting"],
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "firefox-preview",
            {
                "name": _lazy("Firefox Preview"),
                "subtitle": _lazy("Firefox for Android"),
                "extra_fields": [],
                "tags": [],
                "product": "firefox-preview",
                "categories": OrderedDict(
                    [
                        (
                            "install-and-update-firefox-preview",
                            {
                                "name": _lazy("Install and Update"),
                                "topic": "install-and-update",
                                "tags": ["download-and-install"],
                            },
                        ),
                        (
                            "how-to-use-firefox-preview",
                            {
                                "name": _lazy("How do I use Firefox Preview"),
                                "topic": "how-do-i-use-firefox-preview",
                                "tags": ["tips"],
                            },
                        ),
                        (
                            "browsing-firefox-preview",
                            {
                                "name": _lazy("Browsing"),
                                "topic": "browsing-preview",
                                "tags": ["tips"],
                            },
                        ),
                        (
                            "library-firefox-preview",
                            {"name": _lazy("Library"), "topic": "library", "tags": ["library"],},
                        ),
                        (
                            "sync-firefox-preview",
                            {"name": _lazy("Sync"), "topic": "sync-preview", "tags": ["sync"],},
                        ),
                        (
                            "privacy-and-security-firefox-preview",
                            {
                                "name": _lazy("Privacy and Security"),
                                "topic": "privacy-and-security",
                                "tags": ["privacy-and-security"],
                            },
                        ),
                        (
                            "fix-problems-with-firefox-preview",
                            {
                                "name": _lazy("Fix problems with Firefox Preview"),
                                "topic": "fix-problems-firefox-preview",
                                "tags": ["fix-problems"],
                            },
                        ),
                        (
                            "settings-and-preferences-firefox-preview",
                            {
                                "name": _lazy("Settings and Preferences"),
                                "topic": "settings-prefs-preview",
                                "tags": ["customize"],
                            },
                        ),
                        (
                            "advanced-settings-firefox-preview",
                            {
                                "name": _lazy("Advanced Settings"),
                                "topic": "advanced-settings-preview",
                                "tags": ["customize"],
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "firefox-lockwise",
            {
                "name": _lazy("Firefox Lockwise"),
                "subtitle": _lazy("Firefox Lockwise"),
                "extra_fields": [],
                "tags": [],
                "product": "firefox-lockwise",
                "categories": OrderedDict(
                    [
                        (
                            "install-and-set-up",
                            {
                                "name": _lazy("Install and set up"),
                                "topic": "install-lockwise",
                                "tags": ["install-and-set-up"],
                            },
                        ),
                        (
                            "manage-settings-and-logins",
                            {
                                "name": _lazy("Manage settings and logins"),
                                "topic": "lockwise-settings",
                                "tags": ["settings-and-logins"],
                            },
                        ),
                        (
                            "fix-problems-with-firefox-lockwise",
                            {
                                "name": _lazy("Fix problems with Firefox Lockwise"),
                                "topic": "fix-problems-lockwise",
                                "tags": ["fix-problems"],
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "firefox-private-network",
            {
                "name": _lazy("Firefox Private Network Browser-level Protection"),
                "subtitle": _lazy("Firefox Private Network Browser-level Protection"),
                "extra_fields": [],
                "tags": [],
                "product": "firefox-private-network",
                "categories": OrderedDict(
                    [
                        (
                            "get-started",
                            {
                                "name": _lazy("Get started"),
                                "topic": "get-started",
                                "tags": ["get-started"],
                            },
                        ),
                        (
                            "manage-account-and-settings",
                            {
                                "name": _lazy("Manage accounts and settings"),
                                "topic": "manage-account-and-settings",
                                "tags": ["customization"],
                            },
                        ),
                        (
                            "fix-problems",
                            {
                                "name": _lazy("Fix problems with Firefox Private Network"),
                                "topic": "fix-problems",
                                "tags": ["fix-problems"],
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "firefox-private-network-vpn",
            {
                "name": _lazy("Firefox Private Network Device-level Protection"),
                "subtitle": _lazy("Firefox Private Network Device-level Protection"),
                "extra_fields": [],
                "tags": [],
                "product": "firefox-private-network-vpn",
                "categories": OrderedDict(
                    [
                        (
                            "technical",
                            {
                                "name": _lazy("Technical"),
                                "topic": "technical",
                                "tags": ["technical"],
                            },
                        ),
                        (
                            "accounts",
                            {
                                "name": _lazy("Accounts"),
                                "topic": "accounts",
                                "tags": ["accounts"],
                            },
                        ),
                        (
                            "Payments",
                            {
                                "name": _lazy("Payments"),
                                "topic": "payments",
                                "tags": ["payments"],
                            },
                        ),
                        (
                            "Troubleshooting",
                            {
                                "name": _lazy("Troubleshooting"),
                                "topic": "troubleshooting",
                                "tags": ["troubleshooting"],
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)


def add_backtrack_keys(products):
    """Insert 'key' keys so we can go from product or category back to key."""
    for p_k, p_v in products.items():
        p_v["key"] = p_k
        for c_k, c_v in p_v["categories"].items():
            c_v["key"] = c_k


add_backtrack_keys(products)
