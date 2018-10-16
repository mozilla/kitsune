# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kbadge', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='award',
            name='image',
            field=models.ImageField(null=True, upload_to=b'uploads/badges/', blank=True),
        ),
        migrations.AlterField(
            model_name='badge',
            name='image',
            field=models.ImageField(help_text='Must be square. Recommended 256x256.', null=True, upload_to=b'uploads/badges/', blank=True),
        ),
    ]
