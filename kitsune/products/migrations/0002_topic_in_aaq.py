# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='in_aaq',
            field=models.BooleanField(default=False, help_text='Whether this topic is shown to users in the AAQ or not.'),
            preserve_default=True,
        ),
    ]
