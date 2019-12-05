# -*- coding: utf-8 -*-
from django.db import models, migrations
import datetime
import kitsune.tags.models
import kitsune.search.models
from django.conf import settings
import kitsune.sumo.models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('content', models.TextField()),
                ('updated', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('page', models.IntegerField(default=1)),
                ('is_spam', models.BooleanField(default=False)),
                ('marked_as_spam', models.DateTimeField(default=None, null=True)),
                ('creator', models.ForeignKey(related_name='answers', to=settings.AUTH_USER_MODEL)),
                ('marked_as_spam_by', models.ForeignKey(related_name='answers_marked_as_spam', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['created'],
                'permissions': (('bypass_answer_ratelimit', 'Can bypass answering ratelimit'),),
            },
            bases=(models.Model, kitsune.search.models.SearchMixin),
        ),
        migrations.CreateModel(
            name='AnswerVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('helpful', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('anonymous_id', models.CharField(max_length=40, db_index=True)),
                ('answer', models.ForeignKey(related_name='votes', to='questions.Answer')),
                ('creator', models.ForeignKey(related_name='answer_votes', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('num_answers', models.IntegerField(default=0, db_index=True)),
                ('is_locked', models.BooleanField(default=False)),
                ('is_archived', models.NullBooleanField(default=False)),
                ('num_votes_past_week', models.PositiveIntegerField(default=0, db_index=True)),
                ('is_spam', models.BooleanField(default=False)),
                ('marked_as_spam', models.DateTimeField(default=None, null=True)),
                ('locale', kitsune.sumo.models.LocaleField(default=b'en-US', max_length=7, choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bg', '\u0411\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'bs', 'Bosanski'), (b'ca', 'catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'da', 'Dansk'), (b'de', 'Deutsch'), (b'ee', '\xc8\u028begbe'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English'), (b'es', 'Espa\xf1ol'), (b'et', 'eesti keel'), (b'eu', 'Euskara'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge (\xc9ire)'), (b'gl', 'Galego'), (b'gu-IN', '\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ac0'), (b'ha', '\u0647\u064e\u0631\u0652\u0634\u064e\u0646 \u0647\u064e\u0648\u0652\u0633\u064e'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'Magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'As\u1ee5s\u1ee5 Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'km', '\u1781\u17d2\u1798\u17c2\u179a'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'lt', 'lietuvi\u0173 kalba'), (b'ne-NP', '\u0928\u0947\u092a\u093e\u0932\u0940'), (b'nl', 'Nederlands'), (b'no', 'Norsk'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'si', '\u0dc3\u0dd2\u0d82\u0dc4\u0dbd'), (b'sk', 'sloven\u010dina'), (b'sl', 'sloven\u0161\u010dina'), (b'sq', 'Shqip'), (b'sr-Cyrl', '\u0421\u0440\u043f\u0441\u043a\u0438'), (b'sw', 'Kiswahili'), (b'sv', 'Svenska'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'ta-LK', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd (\u0b87\u0bb2\u0b99\u0bcd\u0b95\u0bc8)'), (b'te', '\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41'), (b'th', '\u0e44\u0e17\u0e22'), (b'tr', 'T\xfcrk\xe7e'), (b'uk', '\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430'), (b'ur', '\u0627\u064f\u0631\u062f\u0648'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', '\xe8d\xe8 Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')])),
                ('taken_until', models.DateTimeField(null=True, blank=True)),
                ('creator', models.ForeignKey(related_name='questions', to=settings.AUTH_USER_MODEL)),
                ('last_answer', models.ForeignKey(related_name='last_reply_in', blank=True, to='questions.Answer', null=True)),
                ('marked_as_spam_by', models.ForeignKey(related_name='questions_marked_as_spam', to=settings.AUTH_USER_MODEL, null=True)),
                ('product', models.ForeignKey(related_name='questions', default=None, to='products.Product', null=True)),
                ('solution', models.ForeignKey(related_name='solution_for', to='questions.Answer', null=True)),
                ('tags', kitsune.tags.models.BigVocabTaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags')),
                ('taken_by', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('topic', models.ForeignKey(related_name='questions', to='products.Topic', null=True)),
                ('updated_by', models.ForeignKey(related_name='questions_updated', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-updated'],
                'permissions': (('tag_question', 'Can add tags to and remove tags from questions'), ('change_solution', 'Can change/remove the solution to a question')),
            },
            bases=(models.Model, kitsune.search.models.SearchMixin),
        ),
        migrations.CreateModel(
            name='QuestionLocale',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('locale', kitsune.sumo.models.LocaleField(default=b'en-US', unique=True, max_length=7, choices=[(b'af', 'Afrikaans'), (b'ar', 'Arabic'), (b'az', 'Azerbaijani'), (b'bg', 'Bulgarian'), (b'bn-BD', 'Bengali (Bangladesh)'), (b'bn-IN', 'Bengali (India)'), (b'bs', 'Bosnian'), (b'ca', 'Catalan'), (b'cs', 'Czech'), (b'da', 'Danish'), (b'de', 'German'), (b'ee', 'Ewe'), (b'el', 'Greek'), (b'en-US', 'English'), (b'es', 'Spanish'), (b'et', 'Estonian'), (b'eu', 'Basque'), (b'fa', 'Persian'), (b'fi', 'Finnish'), (b'fr', 'French'), (b'fy-NL', 'Frisian'), (b'ga-IE', 'Irish (Ireland)'), (b'gl', 'Galician'), (b'gu-IN', 'Gujarati'), (b'ha', 'Hausa'), (b'he', 'Hebrew'), (b'hi-IN', 'Hindi (India)'), (b'hr', 'Croatian'), (b'hu', 'Hungarian'), (b'id', 'Indonesian'), (b'ig', 'Igbo'), (b'it', 'Italian'), (b'ja', 'Japanese'), (b'km', 'Khmer'), (b'ko', 'Korean'), (b'ln', 'Lingala'), (b'lt', 'Lithuanian'), (b'ne-NP', 'Nepali'), (b'nl', 'Dutch'), (b'no', 'Norwegian'), (b'pl', 'Polish'), (b'pt-BR', 'Portuguese (Brazilian)'), (b'pt-PT', 'Portuguese (Portugal)'), (b'ro', 'Romanian'), (b'ru', 'Russian'), (b'si', 'Sinhala'), (b'sk', 'Slovak'), (b'sl', 'Slovenian'), (b'sq', 'Albanian'), (b'sr-Cyrl', 'Serbian'), (b'sw', 'Swahili'), (b'sv', 'Swedish'), (b'ta', 'Tamil'), (b'ta-LK', 'Tamil (Sri Lanka)'), (b'te', 'Telugu'), (b'th', 'Thai'), (b'tr', 'Turkish'), (b'uk', 'Ukrainian'), (b'ur', 'Urdu'), (b'vi', 'Vietnamese'), (b'wo', 'Wolof'), (b'xh', 'Xhosa'), (b'yo', 'Yoruba'), (b'zh-CN', 'Chinese (Simplified)'), (b'zh-TW', 'Chinese (Traditional)'), (b'zu', 'Zulu')])),
                ('products', models.ManyToManyField(related_name='questions_locales', to='products.Product')),
            ],
            options={
                'verbose_name': 'AAQ enabled locale',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionMetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField()),
                ('value', models.TextField()),
                ('question', models.ForeignKey(related_name='metadata_set', to='questions.Question')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionVisits',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('visits', models.IntegerField(db_index=True)),
                ('question', models.ForeignKey(to='questions.Question', unique=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('anonymous_id', models.CharField(max_length=40, db_index=True)),
                ('creator', models.ForeignKey(related_name='question_votes', to=settings.AUTH_USER_MODEL, null=True)),
                ('question', models.ForeignKey(related_name='votes', to='questions.Question')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VoteMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('key', models.CharField(max_length=40, db_index=True)),
                ('value', models.CharField(max_length=1000)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='questionmetadata',
            unique_together={('question', 'name')},
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(related_name='answers', to='questions.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='updated_by',
            field=models.ForeignKey(related_name='answers_updated', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
