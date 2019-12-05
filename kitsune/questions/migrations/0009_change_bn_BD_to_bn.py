# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-08-16 18:09
from django.db import migrations


def change_locale_bn_bd_to_bn_forwards(apps, schema_editor):
    Question = apps.get_model("questions", "Question")
    QuestionLocale = apps.get_model("questions", "QuestionLocale")
    Question.objects.filter(locale='bn-BD').update(locale='bn')
    QuestionLocale.objects.filter(locale='bn-BD').update(locale='bn')


def change_locale_bn_to_bn_bd_backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0008_auto_20190507_1052'),
    ]

    operations = [
        migrations.RunPython(change_locale_bn_bd_to_bn_forwards,
                             change_locale_bn_to_bn_bd_backwards)
    ]
