# Generated by Django 4.2.7 on 2024-01-12 10:50
from django.db import migrations
from kitsune.tidings.models import Watch


def clear_watches_for_inactive_users(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Watch = apps.get_model("tidings", "Watch")
    inactive_users = User.objects.filter(is_active=False)
    for user in inactive_users:
        Watch.objects.filter(user=user).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0028_alter_profile_bio_and_upper_name_idx"),
    ]

    operations = [
        migrations.RunPython(clear_watches_for_inactive_users),
    ]
