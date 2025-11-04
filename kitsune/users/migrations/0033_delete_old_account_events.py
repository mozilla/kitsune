from datetime import timedelta

from django.db import migrations
from django.utils import timezone

from kitsune.users import tasks


def cleanup_old_account_events(apps, schema_editor):
    AccountEvent = apps.get_model("users", "AccountEvent")
    two_years_ago = timezone.now() - timedelta(days=730)
    deleted_count = AccountEvent.objects.filter(created_at__lt=two_years_ago).delete()[0]
    print(f"Successfully deleted {deleted_count} old account events")


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0032_profile_account_type_alter_profile_user"),
    ]

    operations = [
        migrations.RunPython(cleanup_old_account_events, migrations.RunPython.noop),
    ]
