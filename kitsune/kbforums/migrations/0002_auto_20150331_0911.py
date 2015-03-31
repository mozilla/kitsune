# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wiki', '0001_initial'),
        ('kbforums', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='document',
            field=models.ForeignKey(to='wiki.Document'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='thread',
            name='last_post',
            field=models.ForeignKey(related_name='last_post_in', to='kbforums.Post', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='creator',
            field=models.ForeignKey(related_name='wiki_post_set', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='thread',
            field=models.ForeignKey(to='kbforums.Thread'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='updated_by',
            field=models.ForeignKey(related_name='wiki_post_last_updated_by', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
