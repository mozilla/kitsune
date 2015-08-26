# -*- coding: utf-8 -*-
"""Migration to change sr-Cyrl locale to sr locale"""

from __future__ import unicode_literals

from django.db import models, migrations


def change_locale_sr_Cyrl_to_sr_forwards(apps, schema_editor):
	WikiMetric = apps.get_model("dashboards", "WikiMetric")
	WikiMetric.objects.filter(locale='sr-Cyrl').update(locale='sr')

def change_locale_sr_Cyrl_to_sr_backwards(apps, schema_editor):
	WikiMetric = apps.get_model("dashboards", "WikiMetric")
	WikiMetric.objects.filter(locale='sr').update(locale='sr-Cyrl')

class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0003_add_top100_to_wikimetric_code_choices'),
    ]

    operations = [
    migrations.RunPython(change_locale_sr_Cyrl_to_sr_forwards, change_locale_sr_Cyrl_to_sr_backwards),
    ]
