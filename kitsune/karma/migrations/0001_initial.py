# -*- coding: utf-8 -*-
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('is_auto', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(help_text=b'Assign this title to these groups.', to='auth.Group', blank=True)),
                ('users', models.ManyToManyField(help_text=b'Assign this title to these users.', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
