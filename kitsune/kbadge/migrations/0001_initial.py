# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


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
                ('image', models.ImageField(null=True, upload_to=b'uploads/badges/', blank=True)),
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
                ('title', models.CharField(help_text='Short, descriptive title', unique=True, max_length=255)),
                ('slug', models.SlugField(help_text='Very short name, for use in URLs and links', unique=True)),
                ('description', models.TextField(help_text='Longer description of the badge and its criteria', blank=True)),
                ('image', models.ImageField(help_text='Must be square. Recommended 256x256.', null=True, upload_to=b'uploads/badges/', blank=True)),
                ('unique', models.BooleanField(default=True, help_text=b'Should awards of this badge be limited to one-per-person?')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(on_delete=models.CASCADE, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-modified', '-created'],
                'db_table': 'badger_badge',
            },
        ),
        migrations.AddField(
            model_name='award',
            name='badge',
            field=models.ForeignKey(on_delete=models.CASCADE, to='kbadge.Badge'),
        ),
        migrations.AddField(
            model_name='award',
            name='creator',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='award_creator', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='award',
            name='user',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='award_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='badge',
            unique_together={('title', 'slug')},
        ),
    ]
