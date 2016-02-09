# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('codename', models.CharField(max_length=100, verbose_name='codename')),
                ('object_id', models.PositiveIntegerField()),
                ('approved', models.BooleanField(default=False, help_text='Designates whether the permission has been approved and treated as active. Unselect this instead of deleting permissions.', verbose_name='approved')),
                ('date_requested', models.DateTimeField(default=datetime.datetime.now, verbose_name='date requested')),
                ('date_approved', models.DateTimeField(null=True, verbose_name='date approved', blank=True)),
                ('content_type', models.ForeignKey(related_name='row_permissions', to='contenttypes.ContentType')),
                ('creator', models.ForeignKey(related_name='created_permissions', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('group', models.ForeignKey(blank=True, to='auth.Group', null=True)),
                ('user', models.ForeignKey(related_name='granted_permissions', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'permission',
                'verbose_name_plural': 'permissions',
                'permissions': (('change_foreign_permissions', 'Can change foreign permissions'), ('delete_foreign_permissions', 'Can delete foreign permissions'), ('approve_permission_requests', 'Can approve permission requests')),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='permission',
            unique_together=set([('codename', 'object_id', 'content_type', 'user', 'group')]),
        ),
    ]
