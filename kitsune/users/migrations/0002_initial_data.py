# -*- coding: utf-8 -*-
from django.db import models, migrations


def create_forum_metrics_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.create(name='Support Forum Tracked')
    Group.objects.create(name='Support Forum Metrics')


def remove_forum_metrics_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Support Forum Tracked', 'Support Forum Metrics']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_forum_metrics_groups, remove_forum_metrics_groups),
    ]
