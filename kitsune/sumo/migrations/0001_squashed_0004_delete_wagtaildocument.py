# Generated by Django 4.2.16 on 2024-10-15 04:32

from django.conf import settings
from django.db import migrations


def create_ratelimit_bypass_perm(apps, schema_editor):
    # First we get or create the content type.
    ContentType = apps.get_model("contenttypes", "ContentType")
    global_permission_ct, created = ContentType.objects.get_or_create(
        model="global_permission", app_label="sumo"
    )

    # Then we create a permission attached to that content type.
    Permission = apps.get_model("auth", "Permission")
    Permission.objects.get_or_create(
        name="Bypass Ratelimits", content_type=global_permission_ct, codename="bypass_ratelimit"
    )


def remove_ratelimit_bypass_perm(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    Permission.objects.filter(codename="bypass_ratelimit").delete()


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# kitsune.sumo.migrations.0001_squashed_0002_initial_data


class Migration(migrations.Migration):

    replaces = [
        ("sumo", "0001_squashed_0002_initial_data"),
        ("sumo", "0003_initial"),
        ("sumo", "0004_delete_wagtaildocument"),
    ]

    initial = True

    dependencies = [
        ("taggit", "0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx"),
        ("contenttypes", "0001_initial"),
        ("auth", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("wagtailcore", "0093_uploadedfile"),
    ]

    operations = [
        migrations.RunPython(
            code=create_ratelimit_bypass_perm,
            reverse_code=remove_ratelimit_bypass_perm,
        ),
    ]
