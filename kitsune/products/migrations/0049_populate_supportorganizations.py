from django.db import migrations


def forward(apps, schema_editor):
    """Give every hybrid_support_groups entry a SupportOrganization row.

    Guarantees M2M ⊆ SupportOrganization: rows that already exist keep their options, and
    rows for groups outside the M2M are left alone. Every M2M entry is copied, including
    ones the model's validation would reject (e.g. a group without a GroupProfile) —
    dropping them here would silently lose support for those groups at cutover; instead
    they surface as admin errors on the row. Exact equality is checked before readers
    move to these rows.
    """
    ProductSupportConfig = apps.get_model("products", "ProductSupportConfig")
    SupportOrganization = apps.get_model("products", "SupportOrganization")

    for config in ProductSupportConfig.objects.all():
        for group in config.hybrid_support_groups.all():
            SupportOrganization.objects.get_or_create(config=config, group=group)


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0048_supportorganization"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
