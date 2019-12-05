# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0003_record'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='record',
            options={'ordering': ['-start_time'], 'permissions': (('reindex', 'Can run a full reindexing'),)},
        ),
    ]
