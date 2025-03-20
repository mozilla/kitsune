from django.db import migrations
from django.core.management import call_command


def cleanup_old_account_events(apps, schema_editor):
    call_command('cleanup_old_account_events')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_profile_account_type_alter_profile_user'),
    ]

    operations = [
        migrations.RunPython(cleanup_old_account_events, migrations.RunPython.noop),
    ]
