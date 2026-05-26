from django.db import migrations


def move_esr_versions_to_firefox(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Version = apps.get_model("products", "Version")

    try:
        firefox = Product.objects.get(slug="firefox")
    except Product.DoesNotExist:
        return

    try:
        firefox_enterprise = Product.objects.get(slug="firefox-enterprise")
    except Product.DoesNotExist:
        return

    esr_versions = Version.objects.filter(
        product=firefox_enterprise, slug__endswith="-esr"
    )

    enterprise_slugs = set(esr_versions.values_list("slug", flat=True))
    clashing = set(
        Version.objects.filter(
            product=firefox, slug__in=enterprise_slugs
        ).values_list("slug", flat=True)
    )
    if clashing:
        # firefox copies are canonical (sync_product_versions writes ESR slugs there now),
        # so drop the stale firefox-enterprise duplicates before moving the rest.
        print(
            f"Dropping {len(clashing)} duplicate ESR version(s) from firefox-enterprise: "
            f"{sorted(clashing)}"
        )
        esr_versions.filter(slug__in=clashing).delete()

    esr_versions.update(product=firefox)


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0035_productsupportconfig_subscription_only_and_more"),
    ]

    operations = [
        migrations.RunPython(move_esr_versions_to_firefox, migrations.RunPython.noop),
    ]
