# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wiki', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('show_after', models.DateTimeField(default=datetime.datetime.now, help_text=b'When this announcement will start appearing. (US/Pacific)', verbose_name=b'Start displaying', db_index=True)),
                ('show_until', models.DateTimeField(help_text=b'When this announcement will stop appearing. Leave blank for indefinite. (US/Pacific)', null=True, verbose_name=b'Stop displaying', db_index=True, blank=True)),
                ('content', models.TextField(help_text=b"Use wiki syntax or HTML. It will display similar to a document's content.", max_length=10000)),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('group', models.ForeignKey(blank=True, to='auth.Group', null=True)),
                ('locale', models.ForeignKey(blank=True, to='wiki.Locale', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
