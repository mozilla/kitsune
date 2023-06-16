# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0002_delete_record'),
    ]

    operations = [
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('batch_id', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=255)),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
                ('start_time', models.DateTimeField(null=True)),
                ('end_time', models.DateTimeField(null=True)),
                ('status', models.IntegerField(default=0, choices=[(0, b'new'), (1, b'in progress'), (2, b'done - fail'), (3, b'done - success')])),
                ('message', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'permissions': (('reindex', 'Can run a full reindexing'),),
            },
            bases=(models.Model,),
        ),
    ]
