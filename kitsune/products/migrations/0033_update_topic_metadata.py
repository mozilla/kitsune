from django.db import migrations


def update_topic_metadata(apps, schema_editor):
    Topic = apps.get_model("products", "Topic")

    for topic in Topic.objects.filter(slug__in=["manage-billing", "manage-subscriptions"]):
        if topic.slug == "manage-billing":
            topic.metadata = {
                "examples": [
                    "Could you update the billing address on my invoices?",
                    "You have the wrong email on my VPN invoice and receipt.",
                ],
                "description": (
                    "Content, questions, or issues related to managing billing for product"
                    " subscriptions (i.e. - adding or removing payment cards, changing billing"
                    " addresses, anything related to invoices or receipts, etc.)."
                ),
            }
        elif topic.slug == "manage-subscriptions":
            topic.metadata = {
                "examples": [
                    "I’d like to request a refund for the charge made to my credit card.",
                ],
                "description": (
                    "Content, questions, or issues related to managing subscriptions to one"
                    " or more of Mozilla's premium products (i.e. - subscription bundling,"
                    " how to cancel or change subscription tiers, requests for refunds, etc.)."
                ),
            }
        topic.save(update_fields=["metadata"])


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0032_zendeskconfig_skip_spam_moderation"),
    ]

    operations = [
        migrations.RunPython(update_topic_metadata, migrations.RunPython.noop),
    ]
