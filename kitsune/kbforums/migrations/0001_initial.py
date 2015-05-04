# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wiki', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('creator', models.ForeignKey(related_name='wiki_post_set', to=settings.AUTH_USER_MODEL)),
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
                ('document', models.ForeignKey(to='wiki.Document')),
                ('last_post', models.ForeignKey(related_name='last_post_in', to='kbforums.Post', null=True)),
            ],
            options={
                'ordering': ['-is_sticky', '-last_post__created'],
                'permissions': (('lock_thread', 'Can lock KB threads'), ('sticky_thread', 'Can sticky KB threads')),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='post',
            name='thread',
            field=models.ForeignKey(to='kbforums.Thread'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='updated_by',
            field=models.ForeignKey(related_name='wiki_post_last_updated_by', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
