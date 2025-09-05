from typing import TypedDict


class TagsDict(TypedDict):
    legacy: str
    tiers: list[str]
    automation: str | None
    segmentation: str | None


class CategoryDict(TypedDict):
    topic: str
    tags: TagsDict


BASE_CATEGORIES: dict[str, CategoryDict] = {
    "payments": {
        "topic": "I need help with a billing or subscription question",
        "tags": {
            "legacy": "payments",
            "tiers": ["t1-billing-and-subscriptions"],
            "automation": None,
            "segmentation": None,
        },
    },
    "accounts_signin": {
        "topic": "I'm having trouble signing into my account/product",
        "tags": {
            "legacy": "accounts",
            "tiers": ["t1-passwords-and-sign-in", "t2-sign-in", "t3-sign-in-failure"],
            "automation": "ssa-sign-in-failure-automation",
            "segmentation": None,
        },
    },
    "general": {
        "topic": "I have feedback or want to request a feature",
        "tags": {
            "legacy": "general",
            "tiers": ["general"],
            "automation": None,
            "segmentation": None,
        },
    },
    "not_listed": {
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
        {**BASE_CATEGORIES["payments"], "slug": "payments"},
        {**BASE_CATEGORIES["accounts_signin"], "slug": "accounts"},
        {
            "slug": "technical",
            "topic": "Mozilla VPN won't connect",
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
            "slug": "technical",
            "topic": "I need help installing or updating my product",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-installation-and-updates"],
                "automation": None,
                "segmentation": None,
            },
        },
        {
            "slug": "technical",
            "topic": "I am having problems selecting a server",
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
        {**BASE_CATEGORIES["general"], "slug": "general"},
        {**BASE_CATEGORIES["not_listed"], "slug": "not_listed"},
    ],
    "firefox-relay": [
        {**BASE_CATEGORIES["payments"], "slug": "payments"},
        {**BASE_CATEGORIES["accounts_signin"], "slug": "accounts"},
        {
            "slug": "technical",
            "topic": "I'm not receiving emails sent to my mask",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-privacy-and-security", "t2-masking", "t3-email-masking"],
                "automation": None,
                "segmentation": "seg-relay-no-fwd-deliver",
            },
        },
        {
            "slug": "technical",
            "topic": "I want to change my email mask domain",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-privacy-and-security", "t2-masking", "t3-email-masking"],
                "automation": None,
                "segmentation": "seg-relay-chg-domain",
            },
        },
        {**BASE_CATEGORIES["general"], "slug": "general"},
        {**BASE_CATEGORIES["not_listed"], "slug": "not_listed"},
    ],
    "mozilla-account": [
        {
            "slug": "accounts",
            "topic": "I need help with Sync (syncing/recovery)",
            "tags": {
                "legacy": "accounts",
                "tiers": ["t1-backup-recovery-and-sync"],
                "automation": "ssa-sync-data-automation",
                "segmentation": None,
            },
        },
        {**BASE_CATEGORIES["accounts_signin"], "slug": "accounts"},
        {
            "slug": "accounts",
            "topic": "I want to delete my account",
            "tags": {
                "legacy": "accounts",
                "tiers": ["t1-accounts", "t2-account-management"],
                "automation": None,
                "segmentation": "seg-acct-delete",
            },
        },
        {**BASE_CATEGORIES["general"], "slug": "general"},
        {**BASE_CATEGORIES["not_listed"], "slug": "not_listed"},
    ],
    "monitor": [
        {**BASE_CATEGORIES["payments"], "slug": "payments"},
        {**BASE_CATEGORIES["accounts_signin"], "slug": "accounts"},
        {
            "slug": "technical",
            "topic": "My removal has been in-progress for a long time",
            "tags": {
                "legacy": "technical",
                "tiers": ["t1-privacy-and-security", "t2-data-removal", "t3-data-brokers"],
                "automation": None,
                "segmentation": "seg-mntor-slow-remove",
            },
        },
        {
            "slug": "technical",
            "topic": "I'm seeing scan results that aren't mine",
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
        {**BASE_CATEGORIES["general"], "slug": "general"},
        {**BASE_CATEGORIES["not_listed"], "slug": "not_listed"},
    ],
    "mdn-plus": [
        {**BASE_CATEGORIES["payments"], "slug": "payments"},
        {**BASE_CATEGORIES["accounts_signin"], "slug": "accounts"},
        {**BASE_CATEGORIES["general"], "slug": "general"},
        {**BASE_CATEGORIES["not_listed"], "slug": "not_listed"},
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
            "topic": "I cant recover my account using email",
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
