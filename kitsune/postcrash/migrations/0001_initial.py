# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0001_squashed_0013_alter_document_related_documents_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Signature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('signature', models.CharField(unique=True, max_length=255, db_index=True)),
                ('document', models.ForeignKey(on_delete=models.CASCADE, to='wiki.Document')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
