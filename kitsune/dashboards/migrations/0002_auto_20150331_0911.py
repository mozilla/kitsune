# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0001_initial'),
        ('wiki', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wikidocumentvisits',
            name='document',
            field=models.ForeignKey(related_name='visits', to='wiki.Document'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='wikidocumentvisits',
            unique_together=set([('period', 'document')]),
        ),
    ]
