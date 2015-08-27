# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_questionlocale(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    QuestionLocale = apps.get_model('questions', 'QuestionLocale')

    p, created = Product.objects.get_or_create(slug='ios', defaults={
        'title': 'Firefox for iOS',
        'description': 'Firefox for iPhone, iPad and iPod touch devices',
        'display_order': 0,
        'visible': False})

    ql, created = QuestionLocale.objects.get_or_create(locale='en-US')
    ql.products.add(p)


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0005_change_locale_sr_Cyrl_to_sr'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_questionlocale),
    ]
