from django.db import migrations


def rename_root(apps, old_slug, new_slug):
    GroupProfile = apps.get_model("groups", "GroupProfile")
    # Slugs are unique across all depths, so any existing holder of the new slug wins.
    if not GroupProfile.objects.filter(slug=new_slug).exists():
        GroupProfile.objects.filter(slug=old_slug, depth=1).update(slug=new_slug)


def forward(apps, schema_editor):
    rename_root(apps, "firefox-enterprise", "professional-support")

    ProductSupportConfig = apps.get_model("products", "ProductSupportConfig")
    configs = ProductSupportConfig.objects.filter(
        product__slug="firefox-enterprise", is_active=True
    )
    configs.filter(forum_config__isnull=False).update(zendesk_config=None)
    for config in configs.filter(forum_config__isnull=True):
        # The unique (product, is_active) constraint allows one inactive config per product.
        ProductSupportConfig.objects.filter(product_id=config.product_id, is_active=False).delete()
        config.is_active = False
        config.save(update_fields=["is_active"])


def backward(apps, schema_editor):
    rename_root(apps, "professional-support", "firefox-enterprise")


class Migration(migrations.Migration):
    dependencies = [
        ("groups", "0014_remove_enterpriseinvitation_support_config"),
        ("products", "0053_organization_routing_help_texts"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
