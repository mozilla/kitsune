# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

# This migration used to create a ios product for the aaq. It was
# incorrect. Since it was deployed, it can't be deleted. So instead it
# is empty.


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0005_change_locale_sr_Cyrl_to_sr'),
    ]

    operations = []
