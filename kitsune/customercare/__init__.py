from typing import TypedDict


class TagsDict(TypedDict):
    legacy: str
    tiers: list[str]
    automation: str | None
    segmentation: str | None


class CategoryDict(TypedDict):
    slug: str
    topic: str
    tags: TagsDict


BASE_CATEGORIES: dict[str, CategoryDict] = {
    "payments": {
        "slug": "payments",
        "topic": "I need help with a billing or subscription question",
        "tags": {
            "legacy": "payments",
            "tiers": ["t1-billing-and-subscriptions"],
            "automation": None,
            "segmentation": None,
        },
    },
    "accounts_signin": {
        "slug": "account-signin",
        "topic": "I can't sign in to my Mozilla account or subscription",
        "tags": {
            "legacy": "accounts",
            "tiers": ["t1-passwords-and-sign-in", "t2-sign-in", "t3-sign-in-failure"],
            "automation": "ssa-sign-in-failure-automation",
            "segmentation": None,
        },
    },
    "general": {
        "slug": "general",
        "topic": "I want to share feedback or suggest a feature",
        "tags": {
            "legacy": "general",
            "tiers": ["general"],
            "automation": None,
            "segmentation": None,
        },
    },
    "not_listed": {
        "slug": "not-listed",
        "topic": "My issue isn't listed here",
        "tags": {
            "legacy": "not_listed",
            "tiers": ["not_listed"],
            "automation": None,
            "segmentation": None,
        },
    },
}

ZENDESK_CATEGORIES = {
    "mozilla-vpn": [
        {
            "slug": "vpn-connection-issues",
            "topic": "I can't connect to Mozilla VPN",
            "tags": {
                "legacy": "technical",
                "tiers": [
                    "t1-performance-and-connectivity",
                    "t2-connectivity",
                    "t3-connection-failure",
                ],
                "automation": "ssa-connection-issues-automation",
                "segmentation": None,
            },
        },
        {
            "slug": "vpn-installation-updates",
            "topic": "I need help installing or updating Mozilla VPN",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-installation-and-updates"],
                "automation": None,
                "segmentation": None,
            },
        },
        {
            "slug": "vpn-server-selection",
            "topic": "I can't choose a VPN location",
            "tags": {
                "legacy": "technical",
                "tiers": [
                    "t1-performance-and-connectivity",
                    "t2-connectivity",
                    "t3-cant-select-server",
                ],
                "automation": None,
                "segmentation": None,
            },
        },
        *BASE_CATEGORIES.values(),
    ],
    "relay": [
        {
            "slug": "relay-email-forwarding",
            "topic": "I'm not receiving emails to my Relay mask",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-privacy-and-security", "t2-masking", "t3-email-masking"],
                "automation": None,
                "segmentation": "seg-relay-no-fwd-deliver",
            },
        },
        {
            "slug": "relay-domain-change",
            "topic": "I want to change my Relay email domain",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-privacy-and-security", "t2-masking", "t3-email-masking"],
                "automation": None,
                "segmentation": "seg-relay-chg-domain",
            },
        },
        *BASE_CATEGORIES.values(),
    ],
    "pocket": [
        {
            "slug": "pocket-saving-highlighting",
            "topic": "I'm having issues with highlighting or saving content",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-privacy-and-security"],
                "automation": None,
                "segmentation": None,
            },
        },
        {
            "slug": "pocket-missing-articles",
            "topic": "My saved articles are missing from my library",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-privacy-and-security"],
                "automation": None,
                "segmentation": None,
            },
        },
        *BASE_CATEGORIES.values(),
    ],
    "mozilla-account": [
        {
            "slug": "mozilla-account-sync",
            "topic": "I need help with Firefox Sync",
            "tags": {
                "legacy": "accounts",
                "tiers": ["t1-backup-recovery-and-sync"],
                "automation": "ssa-sync-data-automation",
                "segmentation": None,
            },
        },
        {
            "slug": "mozilla-account-delete",
            "topic": "I want to delete my Mozilla account",
            "tags": {
                "legacy": "accounts",
                "tiers": ["t1-accounts", "t2-account-management"],
                "automation": None,
                "segmentation": "seg-acct-delete",
            },
        },
        *BASE_CATEGORIES.values(),
    ],
    "monitor": [
        {
            "slug": "monitor-data-removal",
            "topic": "My data removal is taking too long",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-privacy-and-security", "t2-data-removal", "t3-data-brokers"],
                "automation": None,
                "segmentation": "seg-mntor-slow-remove",
            },
        },
        {
            "slug": "monitor-wrong-results",
            "topic": "I'm seeing results that don't belong to me",
            "tags": {
                "legacy": "technical",
                "tiers": [
                    "t1-privacy-and-security",
                    "t2-data-removal",
                    "t3-privacy-protection-scan",
                ],
                "automation": None,
                "segmentation": "seg-mntor-wrong-scan-result",
            },
        },
        *BASE_CATEGORIES.values(),
    ],
    "mdn-plus": [
        *BASE_CATEGORIES.values(),
    ],
}

ZENDESK_CATEGORIES_LOGINLESS = {
    "mozilla-account": [
        {
            "slug": "fxa-2fa-lockout",
            "topic": "My security code isn't working or is lost",
            "tags": {
                "legacy": "accounts",
                "tiers": [
                    "t1-passwords-and-sign-in",
                    "t2-two-factor-authentication",
                    "t3-two-factor-lockout",
                ],
                "automation": "ssa-2fa-automation",
                "segmentation": None,
            },
        },
        {
            "slug": "fxa-emailverify-lockout",
            "topic": "I can't recover my account using email",
            "tags": {
                "legacy": "accounts",
                "tiers": ["t1-passwords-and-sign-in", "t2-sign-in", "t3-email-verify-lockout"],
                "automation": "ssa-pwrdreset-automation",
                "segmentation": None,
            },
        },
        {
            "slug": "fxa-reset-password",
            "topic": "I forgot my password",
            "tags": {
                "legacy": "accounts",
                "tiers": ["t1-passwords-and-sign-in", "t2-reset-passwords"],
                "automation": "ssa-emailverify-automation",
                "segmentation": None,
            },
        },
        {
            "slug": "fxa-remove3rdprtylogin",
            "topic": "I'm having issues signing in with my Google or Apple ID",
            "tags": {
                "legacy": "accounts",
                "tiers": ["t1-passwords-and-sign-in", "t2-sign-in", "t3-3rd-party-sign-in"],
                "automation": None,
                "segmentation": None,
            },
        },
    ]
}
