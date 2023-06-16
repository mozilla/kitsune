# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tidings', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='watch',
            name='email',
            field=models.EmailField(db_index=True, max_length=254, null=True,
                                    blank=True),
        ),
    ]
