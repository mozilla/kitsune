# -*- coding: utf-8 -*-
from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InboxMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.TextField()),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('read', models.BooleanField(default=False, db_index=True)),
                ('replied', models.BooleanField(default=False)),
                ('sender', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('to', models.ForeignKey(related_name='inbox', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'messages_inboxmessage',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OutboxMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.TextField()),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('sender', models.ForeignKey(related_name='outbox', to=settings.AUTH_USER_MODEL)),
                ('to', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'messages_outboxmessage',
            },
            bases=(models.Model,),
        ),
    ]
