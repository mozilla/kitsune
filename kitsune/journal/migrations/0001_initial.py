# -*- coding: utf-8 -*-
from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('level', models.CharField(max_length=20, choices=[('info', 'info'), ('error', 'error')])),
                ('src', models.CharField(max_length=50)),
                ('msg', models.CharField(max_length=255)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
