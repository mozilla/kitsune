# -*- coding: utf-8 -*-
"""Migration to change sr-Cyrl locale to sr locale"""

from django.db import models, migrations


def change_locale_sr_Cyrl_to_sr_forwards(apps, schema_editor):
	Profile = apps.get_model("users", "Profile")
	Profile.objects.filter(locale='sr-Cyrl').update(locale='sr')

def change_locale_sr_Cyrl_to_sr_backwards(apps, schema_editor):
	Profile = apps.get_model("users", "Profile")
	Profile.objects.filter(locale='sr').update(locale='sr-Cyrl')

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20150610_2214'),
    ]

    operations = [
    migrations.RunPython(change_locale_sr_Cyrl_to_sr_forwards, change_locale_sr_Cyrl_to_sr_backwards),
    ]
