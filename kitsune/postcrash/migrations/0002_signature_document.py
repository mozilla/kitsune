# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('postcrash', '0001_initial'),
        ('wiki', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='signature',
            name='document',
            field=models.ForeignKey(to='wiki.Document'),
            preserve_default=True,
        ),
    ]
