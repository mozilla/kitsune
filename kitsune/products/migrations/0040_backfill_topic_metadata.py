from django.db import migrations

# Legacy Zendesk bucket per t1 root, inlined so this migration survives constant deletion.
LEGACY_MAPPING = {
    "accounts": {"t1-accounts", "t1-passwords-and-sign-in", "t1-backup-recovery-and-sync"},
    "technical": {
        "t1-accessibility",
        "t1-browse",
        "t1-download-and-save",
        "t1-email-and-messaging",
        "t1-installation-and-updates",
        "t1-performance-and-connectivity",
        "t1-privacy-and-security",
        "t1-search-tag-and-share",
        "t1-settings",
    },
    "payments": {"t1-billing-and-subscriptions"},
}

EDIT_EMAIL_TIERS = ["t1-accounts", "t2-account-management", "t3-edit-account-details"]
EDIT_EMAIL_AUTOMATION_TAGS = ["ssa-edit-account-details", "loggedin-autosolve"]


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
    ZendeskTopicConfiguration = apps.get_model("products", "ZendeskTopicConfiguration")
    ProductSupportConfig = apps.get_model("products", "ProductSupportConfig")

    # Seed Topic.legacy_tag on t1 roots; only if empty so admin edits are preserved.
    for bucket, t1_tags in LEGACY_MAPPING.items():
        for tier in t1_tags:
            slug = tier[len("t1-") :]
            root = Topic.objects.filter(slug=slug, parent__isnull=True).first()
            if root and not root.legacy_tag:
                root.legacy_tag = bucket
                root.save(update_fields=["legacy_tag"])

    # Form-only entries with tier shapes that don't fit t1-/t2-/t3- (e.g. ['general'],
    # ['not_listed']) stay unlinked so tags_dict falls back to the stored tier_tags JSONField.
    for zd_topic in ZendeskTopic.objects.all():
        update_fields = []

        if zd_topic.automation_tag and not zd_topic.automation_tags:
            zd_topic.automation_tags = [zd_topic.automation_tag]
            update_fields.append("automation_tags")

        if zd_topic.topic_id is None:
            matched = _find_topic_by_tiers(Topic, zd_topic.tier_tags)
            if matched:
                zd_topic.topic = matched
                update_fields.append("topic")

        if update_fields:
            zd_topic.save(update_fields=update_fields)

    # Issue mozilla/sumo#3057: new "change Mozilla account email" entry.
    edit_email_topic = _find_topic_by_tiers(Topic, EDIT_EMAIL_TIERS)
    edit_email_zd, _ = ZendeskTopic.objects.get_or_create(
        slug="mozilla-account-edit-email",
        defaults={
            "form_title": "I want to change the email on my Mozilla account",
            "topic": edit_email_topic,
            "legacy_tag": "accounts",
            "tier_tags": EDIT_EMAIL_TIERS,
            "automation_tag": "",
            "automation_tags": EDIT_EMAIL_AUTOMATION_TAGS,
            "segmentation_tag": "",
        },
    )
    # If the row pre-existed (e.g. manual creation), fill in only the empty fields.
    update_fields = []
    if edit_email_zd.topic_id is None and edit_email_topic is not None:
        edit_email_zd.topic = edit_email_topic
        update_fields.append("topic")
    if not edit_email_zd.automation_tags:
        edit_email_zd.automation_tags = EDIT_EMAIL_AUTOMATION_TAGS
        update_fields.append("automation_tags")
    if update_fields:
        edit_email_zd.save(update_fields=update_fields)

    ma_product = Product.objects.filter(slug="mozilla-account").first()
    if ma_product is None:
        return
    psc = ProductSupportConfig.objects.filter(
        product=ma_product, is_active=True, zendesk_config__isnull=False
    ).first()
    if psc and psc.zendesk_config_id:
        ZendeskTopicConfiguration.objects.get_or_create(
            zendesk_config_id=psc.zendesk_config_id,
            zendesk_topic=edit_email_zd,
            defaults={"display_order": 99, "loginless_only": False},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0039_topic_legacy_tag_zendesktopic_automation_tags_and_more"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
