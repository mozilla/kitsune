# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_update_help_text_email_sent_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'permissions': (('view_karma_points', 'Can view karma points'), ('deactivate_users', 'Can deactivate users'), ('screen_share', 'Can screen share'))},
        ),
    ]
