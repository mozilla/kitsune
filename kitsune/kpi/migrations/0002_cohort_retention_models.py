# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kpi', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cohort',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateField()),
                ('end', models.DateField()),
                ('size', models.PositiveIntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CohortKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RetentionMetric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateField()),
                ('end', models.DateField()),
                ('size', models.PositiveIntegerField(default=0)),
                ('cohort', models.ForeignKey(related_name='retention_metrics', to='kpi.Cohort')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='retentionmetric',
            unique_together=set([('cohort', 'start', 'end')]),
        ),
        migrations.AddField(
            model_name='cohort',
            name='kind',
            field=models.ForeignKey(to='kpi.CohortKind'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='cohort',
            unique_together=set([('kind', 'start', 'end')]),
        ),
    ]
