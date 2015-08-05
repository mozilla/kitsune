# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_waffle_flag(apps, schema_editor):
    Flag = apps.get_model('waffle', 'Flag')
    f = Flag(name='new_aaq', everyone=False, superusers=False, staff=False,
             authenticated=False, rollout=False, testing=False)
    f.save()


def delete_waffle_flag(apps, schema_editor):
    Flag = apps.get_model('waffle', 'Flag')
    f = Flag.objects.get(name='new_aaq')
    f.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('waffle', '0001_initial'),
        ('questions', '0003_auto_20150430_1304'),
    ]

    operations = [
        migrations.RunPython(create_waffle_flag, delete_waffle_flag),
    ]
