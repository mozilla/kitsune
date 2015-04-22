# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Redirect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('product', models.CharField(db_index=True, max_length=30, blank=True)),
                ('version', models.CharField(db_index=True, max_length=30, blank=True)),
                ('platform', models.CharField(db_index=True, max_length=30, blank=True)),
                ('locale', models.CharField(db_index=True, max_length=10, blank=True)),
                ('topic', models.CharField(db_index=True, max_length=50, blank=True)),
                ('target', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='redirect',
            unique_together=set([('product', 'version', 'platform', 'locale', 'topic')]),
        ),
    ]
