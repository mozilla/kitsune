from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("groups", "0013_remove_enterpriseinvitation_completed_actions"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="enterpriseinvitation",
            name="support_config",
        ),
    ]
