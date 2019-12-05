# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imageattachment',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True),
        ),
    ]
