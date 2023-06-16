from django.db import migrations
from django.db.utils import OperationalError


def drop_ghost_columns(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for table_name, column_name in [
            ("badger_award", "claim_code"),
            ("badger_badge", "nominations_accepted"),
            ("badger_badge", "nominations_autoapproved"),
        ]:
            try:
                cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
            except OperationalError:
                # This should only happen if the column doesn't exist.
                pass


class Migration(migrations.Migration):

    dependencies = [
        ("kbadge", "0004_auto_20200629_0826"),
    ]

    operations = [
        migrations.RunPython(drop_ghost_columns, migrations.RunPython.noop),
    ]
