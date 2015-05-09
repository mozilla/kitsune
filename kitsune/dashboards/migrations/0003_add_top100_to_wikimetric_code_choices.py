# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import kitsune.sumo.models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0002_auto_20150430_1304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wikimetric',
            name='code',
            field=models.CharField(db_index=True, max_length=255, choices=[(b'percent_localized_top20', 'Percent Localized: Top 20'), (b'percent_localized_top100', 'Percent Localized: Top 100'), (b'percent_localized_all', 'Percent Localized: All'), (b'active_contributors', 'Monthly Active Contributors')]),
            preserve_default=True,
        ),
    ]
