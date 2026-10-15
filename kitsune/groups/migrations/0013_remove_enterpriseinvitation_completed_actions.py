from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("groups", "0012_enterprise_invitation"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="enterpriseinvitation",
            name="completed_actions",
        ),
    ]
