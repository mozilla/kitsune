# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('starttime', models.DateTimeField(null=True)),
                ('endtime', models.DateTimeField(null=True)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
                'permissions': (('reindex', 'Can run a full reindexing'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Synonym',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_words', models.CharField(max_length=1024)),
                ('to_words', models.CharField(max_length=1024)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
