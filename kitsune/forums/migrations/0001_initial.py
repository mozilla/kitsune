# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import kitsune.search.models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Forum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(null=True)),
                ('display_order', models.IntegerField(default=1, db_index=True)),
                ('is_listed', models.BooleanField(default=True, db_index=True)),
            ],
            options={
                'ordering': ['display_order', 'id'],
                'permissions': (('view_in_forum', 'Can view restricted forums'), ('post_in_forum', 'Can post in restricted forums')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
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
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('forum', models.ForeignKey(to='forums.Forum')),
                ('last_post', models.ForeignKey(related_name='last_post_in', on_delete=django.db.models.deletion.SET_NULL, to='forums.Post', null=True)),
            ],
            options={
                'ordering': ['-is_sticky', '-last_post__created'],
            },
            bases=(models.Model, kitsune.search.models.SearchMixin),
        ),
        migrations.AddField(
            model_name='post',
            name='thread',
            field=models.ForeignKey(to='forums.Thread'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='updated_by',
            field=models.ForeignKey(related_name='post_last_updated_by', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='forum',
            name='last_post',
            field=models.ForeignKey(related_name='last_post_in_forum', on_delete=django.db.models.deletion.SET_NULL, to='forums.Post', null=True),
            preserve_default=True,
        ),
    ]
