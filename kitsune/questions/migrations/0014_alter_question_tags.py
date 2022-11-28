# Generated by Django 3.2.16 on 2022-11-28 06:16

from django.db import migrations
import kitsune.tags.models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0004_alter_taggeditem_content_type_alter_taggeditem_tag'),
        ('questions', '0013_alter_question_is_archived'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='tags',
            field=kitsune.tags.models.BigVocabTaggableManager(help_text='A comma-separated list of tags.', related_name='questions_tagged', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]