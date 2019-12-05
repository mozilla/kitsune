# -*- coding: utf-8 -*-
"""
Add first_answer_email_sent and first_l10n_email_sent fields to Profile.
"""
from django.db import models, migrations
import kitsune.sumo.models  # noqa


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20150430_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='first_answer_email_sent',
            field=models.BooleanField(default=False, help_text='Has been sent a first answer contribution email.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='first_l10n_email_sent',
            field=models.BooleanField(default=False, help_text='Has been sent a first l10n contribution email.'),
            preserve_default=True,
        ),
    ]
