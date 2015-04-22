# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField()),
                ('visible', models.BooleanField(default=False)),
                ('display_order', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, db_index=True)),
                ('slug', models.SlugField()),
                ('description', models.TextField()),
                ('image', models.ImageField(help_text='The image must be 96x96.', max_length=250, null=True, upload_to=b'uploads/products/', blank=True)),
                ('image_offset', models.IntegerField(default=None, null=True, editable=False)),
                ('image_cachebuster', models.CharField(default=None, max_length=32, null=True, editable=False)),
                ('sprite_height', models.IntegerField(default=None, null=True, editable=False)),
                ('display_order', models.IntegerField()),
                ('visible', models.BooleanField(default=False)),
                ('platforms', models.ManyToManyField(to='products.Platform')),
            ],
            options={
                'ordering': ['display_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, db_index=True)),
                ('slug', models.CharField(max_length=255, db_index=True)),
                ('description', models.TextField()),
                ('image', models.ImageField(max_length=250, null=True, upload_to=b'uploads/topics/', blank=True)),
                ('display_order', models.IntegerField()),
                ('visible', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(related_name='subtopics', blank=True, to='products.Topic', null=True)),
                ('product', models.ForeignKey(related_name='topics', to='products.Product')),
            ],
            options={
                'ordering': ['product', 'display_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.CharField(max_length=255, db_index=True)),
                ('min_version', models.FloatField()),
                ('max_version', models.FloatField()),
                ('visible', models.BooleanField(default=False)),
                ('default', models.BooleanField(default=False)),
                ('product', models.ForeignKey(related_name='versions', to='products.Product')),
            ],
            options={
                'ordering': ['-max_version'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='topic',
            unique_together=set([('slug', 'product')]),
        ),
    ]
