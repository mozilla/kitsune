# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


AAQ_LANGUAGES = (
    'en-US',
    'fi',
    'hu',
    'pt-BR',
    'sl',
    'sr-Cyrl',
)


def create_aaq_locales(apps, schema_editor):
    QuestionLocale = apps.get_model('questions', 'QuestionLocale')
    for lang in AAQ_LANGUAGES:
        locale = QuestionLocale(locale=lang)
        locale.save()


def remove_aaq_locales(apps, schema_editor):
    QuestionLocale = apps.get_model('questions', 'QuestionLocale')
    QuestionLocale(locale__in=AAQ_LANGUAGES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_aaq_locales, remove_aaq_locales),
    ]
