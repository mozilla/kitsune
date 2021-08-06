# Generated by Django 2.2.23 on 2021-08-06 09:25

from django.db import migrations
import kitsune.sumo.models


class Migration(migrations.Migration):

    dependencies = [
        ('kbforums', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='content',
            field=kitsune.sumo.models.utf8mb3TextField(html=True),
        ),
        migrations.AlterField(
            model_name='thread',
            name='title',
            field=kitsune.sumo.models.utf8mb3CharField(max_length=255),
        ),
    ]
