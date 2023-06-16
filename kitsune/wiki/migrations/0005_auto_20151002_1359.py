"""Make related_documents optional on Document."""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import kitsune.sumo.models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0004_change_locale_sr_Cyrl_to_sr'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='related_documents',
            field=models.ManyToManyField(related_name='related_documents_rel_+', to='wiki.Document', blank=True),
            preserve_default=True,
        ),
    ]
