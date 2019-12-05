# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kbadge', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE badger_badge SET image = CONCAT('uploads/', image) WHERE image NOT LIKE 'uploads/%' AND image IS NOT NULL AND image != ''"
        )
    ]
