from django.db import migrations
from django.db.models import F

PRODUCT_SLUG = "firefox-enterprise"

# New topics slot in immediately above this one, which stays at the bottom.
ANCHOR_SLUG = "something-else"

# topic_path is the full slug chain from the t1 root: Topic.slug is not unique,
# so a bare slug can match several rows.
ZD_TOPICS = [
    {
        "slug": "configuring-or-troubleshooting-pdf-js",
        "form_title": "Configuring or troubleshooting PDF.js",
        "topic_path": ["browse", "images-and-documents", "pdfs"],
        "tier_tags": ["t1-browse", "t2-images-and-documents", "t3-pdfs"],
        "legacy_tag": "technical",
    },
    {
        "slug": "issues-accessing-firefox-services-or-infrastructure",
        "form_title": "Issues accessing Firefox services or infrastructure",
        "topic_path": ["performance-and-connectivity"],
        "tier_tags": ["t1-performance-and-connectivity"],
        "legacy_tag": "technical",
    },
    {
        "slug": "report-security-concerns-or-suspected-vulnerabilities",
        "form_title": "Report security concerns or suspected vulnerabilities",
        "topic_path": ["privacy-and-security", "security"],
        "tier_tags": ["t1-privacy-and-security", "t2-security"],
        "legacy_tag": "technical",
    },
]


def _resolve_topic(Topic, topic_path):
    """Return the one active Topic matching the slug chain, or None if it isn't unique."""
    lookup = {"slug": topic_path[-1], "is_archived": False}
    prefix = "parent__"
    for slug in reversed(topic_path[:-1]):
        lookup[f"{prefix}slug"] = slug
        prefix += "parent__"
    lookup[f"{prefix}isnull"] = True

    try:
        return Topic.objects.get(**lookup)
    except Topic.DoesNotExist, Topic.MultipleObjectsReturned:
        return None


def _zendesk_config(apps):
    """Return the Zendesk config for the product, or None if there isn't exactly one."""
    ProductSupportConfig = apps.get_model("products", "ProductSupportConfig")
    try:
        support_config = ProductSupportConfig.objects.select_related("zendesk_config").get(
            product__slug=PRODUCT_SLUG, is_active=True
        )
    except ProductSupportConfig.DoesNotExist, ProductSupportConfig.MultipleObjectsReturned:
        return None
    return support_config.zendesk_config


def _insertion_order(ZendeskTopicConfiguration, config, count):
    """Order for the first new row, making room above the anchor if it's there."""
    rows = ZendeskTopicConfiguration.objects.filter(zendesk_config=config)
    anchor = rows.filter(zendesk_topic__slug=ANCHOR_SLUG).first()
    if anchor is None:
        orders = list(rows.values_list("display_order", flat=True))
        return (max(orders) + 1) if orders else 0
    rows.filter(display_order__gte=anchor.display_order).update(
        display_order=F("display_order") + count
    )
    return anchor.display_order


def forward(apps, schema_editor):
    Topic = apps.get_model("products", "Topic")
    ZendeskTopic = apps.get_model("products", "ZendeskTopic")
    ZendeskTopicConfiguration = apps.get_model("products", "ZendeskTopicConfiguration")

    config = _zendesk_config(apps)
    if config is None:
        return

    pending = []
    for entry in ZD_TOPICS:
        topic = _resolve_topic(Topic, entry["topic_path"])
        if topic is None:
            continue
        zd_topic, _ = ZendeskTopic.objects.get_or_create(
            slug=entry["slug"],
            defaults={
                "form_title": entry["form_title"],
                "topic": topic,
                "tier_tags": entry["tier_tags"],
                "legacy_tag": entry["legacy_tag"],
                "automation_tags": [],
            },
        )
        already_linked = ZendeskTopicConfiguration.objects.filter(
            zendesk_config=config, zendesk_topic=zd_topic
        ).exists()
        if not already_linked:
            pending.append(zd_topic)

    if not pending:
        return

    start = _insertion_order(ZendeskTopicConfiguration, config, len(pending))
    for offset, zd_topic in enumerate(pending):
        ZendeskTopicConfiguration.objects.create(
            zendesk_config=config,
            zendesk_topic=zd_topic,
            display_order=start + offset,
            loginless_only=False,
        )


def backward(apps, schema_editor):
    ZendeskTopic = apps.get_model("products", "ZendeskTopic")
    ZendeskTopicConfiguration = apps.get_model("products", "ZendeskTopicConfiguration")

    slugs = [entry["slug"] for entry in ZD_TOPICS]
    config = _zendesk_config(apps)
    if config is not None:
        ZendeskTopicConfiguration.objects.filter(
            zendesk_config=config, zendesk_topic__slug__in=slugs
        ).delete()
    # Leave topics alone if another config picked them up.
    ZendeskTopic.objects.filter(slug__in=slugs, configurations__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0045_zendeskconfig_enable_urgency_field"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
