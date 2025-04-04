# Generated by Django 4.2.16 on 2024-11-15 02:38

from django.db import migrations
import kitsune.tags.models


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0001_initial"),
        ("wiki", "0016_alter_document_contributors"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="tags",
            field=kitsune.tags.models.BigVocabTaggableManager(
                help_text="A comma-separated list of tags.",
                through="tags.SumoTaggedItem",
                to="tags.SumoTag",
                verbose_name="Tags",
            ),
        ),
    ]
