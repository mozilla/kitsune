# -*- coding: utf-8 -*-
"""Migration to change sr-Cyrl locale to sr locale"""

from __future__ import unicode_literals

from django.db import models, migrations


def change_locale_sr_Cyrl_to_sr_forwards(apps, schema_editor):
	Document = apps.get_model("wiki", "Document")
	Locale = apps.get_model("wiki", "Locale")
	Document.objects.filter(locale='sr-Cyrl').update(locale='sr')
	Locale.objects.filter(locale='sr-Cyrl').update(locale='sr')

def change_locale_sr_Cyrl_to_sr_backwards(apps, schema_editor):
	Document = apps.get_model("wiki", "Document")
	Locale = apps.get_model("wiki", "Locale")
	Document.objects.filter(locale='sr').update(locale='sr-Cyrl')
	Locale.objects.filter(locale='sr').update(locale='sr-Cyrl')

class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0003_add_related_documents_field'),
    ]

    operations = [
    migrations.RunPython(change_locale_sr_Cyrl_to_sr_forwards, change_locale_sr_Cyrl_to_sr_backwards),
    ]
