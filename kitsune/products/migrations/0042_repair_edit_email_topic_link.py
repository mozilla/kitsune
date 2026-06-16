from django.db import migrations

# Backfill topic FK + product links so the classifier can resolve automation tags
# for these ZendeskTopics; idempotent so manual fixes and fresh DBs are no-ops.
CONNECTIONS = [
    {
        "zendesk_slug": "mozilla-account-edit-email",
        "target_tiers": ["t1-accounts", "t2-account-management", "t3-edit-account-details"],
        "automation_tags": ["ssa-edit-account-details", "loggedin-autosolve"],
        "product_slugs": ["mozilla-account"],
    },
    {
        "zendesk_slug": "fxa-emailverify-lockout",
        "target_tiers": ["t1-passwords-and-sign-in", "t2-sign-in", "t3-email-verify-lockout"],
        "automation_tags": ["ssa-pwrdreset-automation"],
        "product_slugs": ["mozilla-account"],
    },
    {
        "zendesk_slug": "account-signin",
        "target_tiers": ["t1-passwords-and-sign-in", "t2-sign-in", "t3-sign-in-failure"],
        "automation_tags": ["ssa-sign-in-failure-automation"],
        "product_slugs": [
            "firefox",
            "firefox-enterprise",
            "monitor",
            "mozilla-account",
            "mozilla-vpn",
            "pocket",
        ],
    },
    {
        "zendesk_slug": "vpn-connection-issues",
        "target_tiers": [
            "t1-performance-and-connectivity",
            "t2-connectivity",
            "t3-connection-failure",
        ],
        "automation_tags": ["ssa-connection-issues-automation"],
        "product_slugs": ["mozilla-vpn"],
    },
]


def _find_topic_by_tiers(Topic, tier_tags):
    current = None
    for i, tier in enumerate(tier_tags, start=1):
        prefix = f"t{i}-"
        if not tier.startswith(prefix):
            return None
        slug = tier[len(prefix) :]
        qs = Topic.objects.filter(slug=slug)
        qs = qs.filter(parent__isnull=True) if current is None else qs.filter(parent=current)
        current = qs.first()
        if current is None:
            return None
    return current


def forward(apps, schema_editor):
    Topic = apps.get_model("products", "Topic")
    Product = apps.get_model("products", "Product")
    ZendeskTopic = apps.get_model("products", "ZendeskTopic")
    ProductTopic = apps.get_model("products", "ProductTopic")

    for conn in CONNECTIONS:
        zd_topic = ZendeskTopic.objects.filter(slug=conn["zendesk_slug"]).first()
        if zd_topic is None:
            continue

        target_topic = _find_topic_by_tiers(Topic, conn["target_tiers"])
        leaf_slug = conn["target_tiers"][-1].split("-", 1)[1]

        if target_topic is not None and not (
            zd_topic.topic_id and zd_topic.topic.slug == leaf_slug
        ):
            zd_topic.topic = target_topic
            zd_topic.save(update_fields=["topic"])

        if zd_topic.automation_tags != conn["automation_tags"]:
            zd_topic.automation_tags = conn["automation_tags"]
            zd_topic.save(update_fields=["automation_tags"])

        topic_for_product = zd_topic.topic if zd_topic.topic_id else target_topic
        if topic_for_product is None:
            continue
        for product_slug in conn["product_slugs"]:
            product = Product.objects.filter(slug=product_slug).first()
            if product is not None:
                ProductTopic.objects.get_or_create(product=product, topic=topic_for_product)


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0041_remove_zendesktopic_automation_tag"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
