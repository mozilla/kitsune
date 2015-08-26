# -*- coding: utf-8 -*-
"""Migration to change sr-Cyrl locale to sr locale"""

from __future__ import unicode_literals

from django.db import models, migrations


def change_locale_sr_Cyrl_to_sr_forwards(apps, schema_editor):
	Image = apps.get_model("gallery", "Image")
	Video = apps.get_model("gallery", "Video")
	Image.objects.filter(locale='sr-Cyrl').update(locale='sr')
	Video.objects.filter(locale='sr-Cyrl').update(locale='sr')

def change_locale_sr_Cyrl_to_sr_backwards(apps, schema_editor):
	Image = apps.get_model("gallery", "Image")
	Video = apps.get_model("gallery", "Video")
	Image.objects.filter(locale='sr').update(locale='sr-Cyrl')
	Video.objects.filter(locale='sr').update(locale='sr-Cyrl')

class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0002_auto_20150430_1304'),
    ]

    operations = [
    migrations.RunPython(change_locale_sr_Cyrl_to_sr_forwards, change_locale_sr_Cyrl_to_sr_backwards),
    ]
