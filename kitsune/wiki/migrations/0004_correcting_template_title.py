# -*- coding: utf-8 -*-
"""Migration to correct the wrong title of Template Catagory Documents"""
from __future__ import unicode_literals

from django.db import models, migrations
import kitsune.wiki.models
from kitsune.wiki.config import TEMPLATES_CATEGORY


def correct_template_title(apps, schema_editor):
	Document = apps.get_model("wiki", "Document")
	for document in Document.objects.filter(
		category=TEMPLATES_CATEGORY).exclude(
		title__startswith='Template:'):

		document.title = document.title.split(':')[-1]
		document.title = 'Template:' + document.title
		document.save()

def reverse_correct_template_title(apps, schema_editor):
	raise RuntimeError('Cannot reverse this migration.')


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0003_add_related_documents_field'),
    ]

    operations = [
    migrations.RunPython(correct_template_title, reverse_correct_template_title),
    ]
