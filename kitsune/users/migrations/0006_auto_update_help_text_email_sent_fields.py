# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import kitsune.sumo.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_set_initial_contrib_email_flag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='first_l10n_email_sent',
            field=models.BooleanField(default=False, help_text=u'Has been sent a first revision contribution email.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='first_answer_email_sent',
            field=models.BooleanField(default=False, help_text=u'Has been sent a first answer contribution email.'),
            preserve_default=True,
        ),
    ]
