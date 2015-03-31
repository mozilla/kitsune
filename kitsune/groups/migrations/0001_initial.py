# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True, max_length=80, editable=False)),
                ('information', models.TextField(help_text='Use Wiki Syntax')),
                ('information_html', models.TextField(editable=False)),
                ('avatar', models.ImageField(max_length=250, upload_to=b'uploads/groupavatars/', null=True, verbose_name='Avatar', blank=True)),
                ('group', models.ForeignKey(related_name='profile', to='auth.Group')),
                ('leaders', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['slug'],
            },
            bases=(models.Model,),
        ),
    ]
