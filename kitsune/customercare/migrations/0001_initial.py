# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import kitsune.search.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Reply',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('twitter_username', models.CharField(max_length=20)),
                ('tweet_id', models.BigIntegerField()),
                ('raw_json', models.TextField()),
                ('locale', models.CharField(max_length=20)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('reply_to_tweet_id', models.BigIntegerField()),
                ('user', models.ForeignKey(related_name='tweet_replies', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, kitsune.search.models.SearchMixin),
        ),
        migrations.CreateModel(
            name='Tweet',
            fields=[
                ('tweet_id', models.BigIntegerField(serialize=False, primary_key=True)),
                ('raw_json', models.TextField()),
                ('locale', models.CharField(max_length=20, db_index=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('hidden', models.BooleanField(default=False, db_index=True)),
                ('reply_to', models.ForeignKey(related_name='replies', to='customercare.Tweet', null=True)),
            ],
            options={
                'ordering': ('-tweet_id',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TwitterAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=15)),
                ('banned', models.BooleanField(default=False, db_index=True)),
                ('ignored', models.BooleanField(default=False, db_index=True)),
            ],
            options={
                'permissions': (('ban_account', 'Can ban twitter accounts'), ('ignore_account', 'Can tag accounts to ignore')),
            },
            bases=(models.Model,),
        ),
    ]
