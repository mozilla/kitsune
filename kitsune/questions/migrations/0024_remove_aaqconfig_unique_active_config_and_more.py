from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("questions", "0023_alter_answer_created_alter_answer_updated_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="aaqconfig",
            name="unique_active_config",
        ),
        migrations.RemoveField(
            model_name="aaqconfig",
            name="product",
        ),
        migrations.RemoveField(
            model_name="aaqconfig",
            name="is_active",
        ),
    ]
