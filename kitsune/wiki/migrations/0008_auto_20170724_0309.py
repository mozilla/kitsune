# -*- coding: utf-8 -*-
from django.db import migrations


def add_malay(apps, schema_editor):
    Locale = apps.get_model('wiki', 'Locale')
    Locale.objects.get_or_create(locale='ms')


def remove_malay(apps, schema_editor):
    Locale = apps.get_model('wiki', 'Locale')
    Locale.objects.filter(locale='ms').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0007_draftrevision'),
    ]

    operations = [
            migrations.RunPython(add_malay, remove_malay),
    ]
