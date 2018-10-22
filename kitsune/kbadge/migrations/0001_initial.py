# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import kitsune.kbadge.models
from django.conf import settings
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Award',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(help_text=b'Explanation and evidence for the badge award', blank=True)),
                ('image', models.ImageField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/uploads/', location=b'/app/media/uploads'), null=True, upload_to=kitsune.kbadge.models.UploadTo(b'image', b'png'), blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-modified', '-created'],
                'db_table': 'badger_award',
            },
        ),
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Short, descriptive title', unique=True, max_length=255)),
                ('slug', models.SlugField(help_text=b'Very short name, for use in URLs and links', unique=True)),
                ('description', models.TextField(help_text=b'Longer description of the badge and its criteria', blank=True)),
                # TODO: delete reference to UploadTo class below (so we can delete the class from ../models.py)
                ('image', models.ImageField(help_text=b'Upload an image to represent the badge', storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/uploads/', location=b'/app/media/uploads'), null=True, upload_to=kitsune.kbadge.models.UploadTo(b'image', b'png'), blank=True)),
                ('unique', models.BooleanField(default=True, help_text=b'Should awards of this badge be limited to one-per-person?')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-modified', '-created'],
                'db_table': 'badger_badge',
            },
        ),
        migrations.AddField(
            model_name='award',
            name='badge',
            field=models.ForeignKey(to='kbadge.Badge'),
        ),
        migrations.AddField(
            model_name='award',
            name='creator',
            field=models.ForeignKey(related_name='award_creator', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='award',
            name='user',
            field=models.ForeignKey(related_name='award_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='badge',
            unique_together=set([('title', 'slug')]),
        ),
    ]
