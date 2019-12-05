# -*- coding: utf-8 -*-
from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlaggedObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('status', models.IntegerField(default=0, db_index=True, choices=[(0, 'Pending'), (1, 'Accepted and Fixed'), (2, 'Rejected')])),
                ('reason', models.CharField(max_length=64, choices=[(b'spam', 'Spam or other unrelated content'), (b'language', 'Inappropriate language/dialog'), (b'bug_support', 'Misplaced bug report or support request'), (b'abuse', 'Abusive content'), (b'other', 'Other (please specify)')])),
                ('notes', models.TextField(default=b'', blank=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('handled', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('creator', models.ForeignKey(related_name='flags', to=settings.AUTH_USER_MODEL)),
                ('handled_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['created'],
                'permissions': (('can_moderate', 'Can moderate flagged objects'),),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='flaggedobject',
            unique_together=set([('content_type', 'object_id', 'creator')]),
        ),
    ]
