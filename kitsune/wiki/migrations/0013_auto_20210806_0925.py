# Generated by Django 2.2.23 on 2021-08-06 09:25

from django.db import migrations
import kitsune.sumo.models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0012_auto_20200629_0826'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='html',
            field=kitsune.sumo.models.utf8mb3TextField(editable=False, html=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='needs_change_comment',
            field=kitsune.sumo.models.utf8mb3CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='document',
            name='slug',
            field=kitsune.sumo.models.utf8mb3CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='document',
            name='title',
            field=kitsune.sumo.models.utf8mb3CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='draftrevision',
            name='content',
            field=kitsune.sumo.models.utf8mb3TextField(blank=True, html=True),
        ),
        migrations.AlterField(
            model_name='draftrevision',
            name='keywords',
            field=kitsune.sumo.models.utf8mb3CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='draftrevision',
            name='slug',
            field=kitsune.sumo.models.utf8mb3CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='draftrevision',
            name='summary',
            field=kitsune.sumo.models.utf8mb3TextField(blank=True, html=True),
        ),
        migrations.AlterField(
            model_name='draftrevision',
            name='title',
            field=kitsune.sumo.models.utf8mb3CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='revision',
            name='comment',
            field=kitsune.sumo.models.utf8mb3CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='revision',
            name='content',
            field=kitsune.sumo.models.utf8mb3TextField(html=True),
        ),
        migrations.AlterField(
            model_name='revision',
            name='keywords',
            field=kitsune.sumo.models.utf8mb3CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='revision',
            name='summary',
            field=kitsune.sumo.models.utf8mb3TextField(html=True),
        ),
    ]
