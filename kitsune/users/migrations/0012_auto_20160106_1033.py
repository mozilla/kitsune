# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_add_csat_email_sent_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailchange',
            name='email',
            field=models.EmailField(max_length=254, null=True, db_index=True),
        ),
    ]
