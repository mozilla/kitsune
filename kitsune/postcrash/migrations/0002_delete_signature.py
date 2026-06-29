from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("postcrash", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Signature",
        ),
    ]
