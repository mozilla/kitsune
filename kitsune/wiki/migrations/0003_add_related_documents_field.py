# -*- coding: utf-8 -*-
"""Migration to add the related_documents M2M field to the Document model."""
from __future__ import unicode_literals

from django.db import models, migrations
import kitsune.sumo.models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0002_auto_20150430_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='related_documents',
            field=models.ManyToManyField(related_name='related_documents_rel_+', to='wiki.Document'),
            preserve_default=True,
        ),
    ]
