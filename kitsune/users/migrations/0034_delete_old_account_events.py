from django.db import migrations
from django.utils import timezone
from datetime import timedelta


def delete_old_account_events(apps, schema_editor):
    AccountEvent = apps.get_model('users', 'AccountEvent')
    two_years_ago = timezone.now() - timedelta(days=730)  # 2 years * 365 days
    AccountEvent.objects.filter(created_at__lt=two_years_ago).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_profile_account_type_alter_profile_user'),
    ]

    operations = [
        migrations.RunPython(delete_old_account_events, migrations.RunPython.noop),
    ]
