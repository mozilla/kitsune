# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_ratelimit_bypass_perm(apps, schema_editor):
    # First we get or create the content type.
    ContentType = apps.get_model('contenttypes', 'ContentType')
    global_permission_ct, created = ContentType.objects.get_or_create(
        model='global_permission', app_label='sumo')

    # Then we create a permission attached to that content type.
    Permission = apps.get_model('auth', 'Permission')
    perm = Permission.objects.create(
        name='Bypass Ratelimits',
        content_type=global_permission_ct,
        codename='bypass_ratelimit')


def remove_ratelimit_bypass_perm(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    perm = Permission.objects.filter(codename='bypass_ratelimit').delete()


def create_treejack_switch(apps, schema_editor):
    Switch = apps.get_model('waffle', 'Switch')
    Switch.objects.create(
        name='treejack',
        note='Enables/disables the Treejack snippet.',
        active=False)


def remove_treejack_switch(apps, schema_editor):
    Switch = apps.get_model('waffle', 'Switch')
    Switch.objects.filter(name='treejack').delete()


def create_refresh_survey_flag(apps, schema_editor):
    Sample = apps.get_model('waffle', 'Sample')
    Sample.objects.get_or_create(
        name='refresh-survey',
        note='Samples users that refresh Firefox to give them a survey.',
        percent=50.0)


def remove_refresh_survey_flag(apps, schema_editor):
    Sample = apps.get_model('waffle', 'Sample')
    Sample.objects.filter(name='refresh-survey').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sumo', '0001_initial'),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
        ('waffle', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_ratelimit_bypass_perm, remove_ratelimit_bypass_perm),
        migrations.RunPython(create_treejack_switch, remove_treejack_switch),
        migrations.RunPython(create_refresh_survey_flag, remove_refresh_survey_flag),
    ]
