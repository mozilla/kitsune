from django.db import migrations


def forward(apps, schema_editor):
    """Copy all legacy assignments, preserving existing organization rows and options.

    Include groups rejected by current validation to avoid silently losing support.
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
