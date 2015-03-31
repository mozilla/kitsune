# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
            ],
            options={
                'ordering': ['created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('replies', models.IntegerField(default=0)),
                ('is_locked', models.BooleanField(default=False)),
                ('is_sticky', models.BooleanField(default=False, db_index=True)),
                ('creator', models.ForeignKey(related_name='wiki_thread_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-is_sticky', '-last_post__created'],
                'permissions': (('lock_thread', 'Can lock KB threads'), ('sticky_thread', 'Can sticky KB threads')),
            },
            bases=(models.Model,),
        ),
    ]
