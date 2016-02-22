# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20151110_1307'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='csat_email_sent',
            field=models.DateField(null=True, verbose_name='When the user was sent a community health survey', blank=True),
            preserve_default=True,
        ),
    ]
