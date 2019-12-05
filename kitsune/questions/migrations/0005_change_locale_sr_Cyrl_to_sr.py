# -*- coding: utf-8 -*-
"""Migration to change sr-Cyrl locale to sr locale"""
from django.db import models, migrations


def change_locale_sr_Cyrl_to_sr_forwards(apps, schema_editor):
	Question = apps.get_model("questions", "Question")
	QuestionLocale = apps.get_model("questions", "QuestionLocale")
	Question.objects.filter(locale='sr-Cyrl').update(locale='sr')
	QuestionLocale.objects.filter(locale='sr-Cyrl').update(locale='sr')

def change_locale_sr_Cyrl_to_sr_backwards(apps, schema_editor):
	Question = apps.get_model("questions", "Question")
	QuestionLocale = apps.get_model("questions", "QuestionLocale")
	Question.objects.filter(locale='sr').update(locale='sr-Cyrl')
	QuestionLocale.objects.filter(locale='sr').update(locale='sr-Cyrl')

class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0004_new_aaq_waffle_flag'),
    ]

    operations = [
    migrations.RunPython(change_locale_sr_Cyrl_to_sr_forwards, change_locale_sr_Cyrl_to_sr_backwards),
    ]
