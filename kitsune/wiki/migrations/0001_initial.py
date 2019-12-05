# -*- coding: utf-8 -*-
from django.db import models, migrations
import datetime
import kitsune.wiki.permissions
import kitsune.tags.models
import kitsune.search.models
from django.conf import settings
import kitsune.sumo.models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, db_index=True)),
                ('slug', models.CharField(max_length=255, db_index=True)),
                ('is_template', models.BooleanField(default=False, db_index=True, editable=False)),
                ('is_localizable', models.BooleanField(default=True, db_index=True)),
                ('locale', kitsune.sumo.models.LocaleField(default=b'en-US', max_length=7, db_index=True, choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bg', '\u0411\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'bs', 'Bosanski'), (b'ca', 'catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'da', 'Dansk'), (b'de', 'Deutsch'), (b'ee', '\xc8\u028begbe'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English'), (b'es', 'Espa\xf1ol'), (b'et', 'eesti keel'), (b'eu', 'Euskara'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge (\xc9ire)'), (b'gl', 'Galego'), (b'gu-IN', '\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ac0'), (b'ha', '\u0647\u064e\u0631\u0652\u0634\u064e\u0646 \u0647\u064e\u0648\u0652\u0633\u064e'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'Magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'As\u1ee5s\u1ee5 Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'km', '\u1781\u17d2\u1798\u17c2\u179a'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'lt', 'lietuvi\u0173 kalba'), (b'ne-NP', '\u0928\u0947\u092a\u093e\u0932\u0940'), (b'nl', 'Nederlands'), (b'no', 'Norsk'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'si', '\u0dc3\u0dd2\u0d82\u0dc4\u0dbd'), (b'sk', 'sloven\u010dina'), (b'sl', 'sloven\u0161\u010dina'), (b'sq', 'Shqip'), (b'sr-Cyrl', '\u0421\u0440\u043f\u0441\u043a\u0438'), (b'sw', 'Kiswahili'), (b'sv', 'Svenska'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'ta-LK', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd (\u0b87\u0bb2\u0b99\u0bcd\u0b95\u0bc8)'), (b'te', '\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41'), (b'th', '\u0e44\u0e17\u0e22'), (b'tr', 'T\xfcrk\xe7e'), (b'uk', '\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430'), (b'ur', '\u0627\u064f\u0631\u062f\u0648'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', '\xe8d\xe8 Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')])),
                ('html', models.TextField(editable=False)),
                ('category', models.IntegerField(db_index=True, choices=[(10, 'Troubleshooting'), (20, 'How to'), (30, 'How to contribute'), (40, 'Administration'), (50, 'Navigation'), (60, 'Templates'), (70, 'Canned Responses')])),
                ('is_archived', models.BooleanField(default=False, help_text='If checked, this wiki page will be hidden from basic searches and dashboards. When viewed, the page will warn that it is no longer maintained.', db_index=True, verbose_name=b'is obsolete')),
                ('allow_discussion', models.BooleanField(default=True, help_text='If checked, this document allows discussion in an associated forum. Uncheck to hide/disable the forum.')),
                ('needs_change', models.BooleanField(default=False, help_text='If checked, this document needs updates.', db_index=True)),
                ('needs_change_comment', models.CharField(max_length=500, blank=True)),
                ('share_link', models.CharField(default=b'', max_length=24)),
                ('display_order', models.IntegerField(default=1, db_index=True)),
                ('contributors', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': [('archive_document', 'Can archive document'), ('edit_needs_change', 'Can edit needs_change')],
            },
            bases=(models.Model, kitsune.search.models.SearchMixin, kitsune.wiki.permissions.DocumentPermissionMixin),
        ),
        migrations.CreateModel(
            name='DocumentImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document', models.ForeignKey(to='wiki.Document')),
                ('image', models.ForeignKey(to='gallery.Image')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DocumentLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(max_length=16)),
                ('linked_from', models.ForeignKey(related_name='documentlink_to_set', to='wiki.Document')),
                ('linked_to', models.ForeignKey(related_name='documentlink_from_set', to='wiki.Document')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HelpfulVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('helpful', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('anonymous_id', models.CharField(max_length=40, db_index=True)),
                ('user_agent', models.CharField(max_length=1000)),
                ('creator', models.ForeignKey(related_name='poll_votes', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HelpfulVoteMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=40, db_index=True)),
                ('value', models.CharField(max_length=1000)),
                ('vote', models.ForeignKey(related_name='metadata', to='wiki.HelpfulVote')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImportantDate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=100)),
                ('date', models.DateField(db_index=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Locale',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('locale', kitsune.sumo.models.LocaleField(default=b'en-US', max_length=7, db_index=True, choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bg', '\u0411\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'bs', 'Bosanski'), (b'ca', 'catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'da', 'Dansk'), (b'de', 'Deutsch'), (b'ee', '\xc8\u028begbe'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English'), (b'es', 'Espa\xf1ol'), (b'et', 'eesti keel'), (b'eu', 'Euskara'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge (\xc9ire)'), (b'gl', 'Galego'), (b'gu-IN', '\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ac0'), (b'ha', '\u0647\u064e\u0631\u0652\u0634\u064e\u0646 \u0647\u064e\u0648\u0652\u0633\u064e'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'Magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'As\u1ee5s\u1ee5 Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'km', '\u1781\u17d2\u1798\u17c2\u179a'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'lt', 'lietuvi\u0173 kalba'), (b'ne-NP', '\u0928\u0947\u092a\u093e\u0932\u0940'), (b'nl', 'Nederlands'), (b'no', 'Norsk'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'si', '\u0dc3\u0dd2\u0d82\u0dc4\u0dbd'), (b'sk', 'sloven\u010dina'), (b'sl', 'sloven\u0161\u010dina'), (b'sq', 'Shqip'), (b'sr-Cyrl', '\u0421\u0440\u043f\u0441\u043a\u0438'), (b'sw', 'Kiswahili'), (b'sv', 'Svenska'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'ta-LK', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd (\u0b87\u0bb2\u0b99\u0bcd\u0b95\u0bc8)'), (b'te', '\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41'), (b'th', '\u0e44\u0e17\u0e22'), (b'tr', 'T\xfcrk\xe7e'), (b'uk', '\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430'), (b'ur', '\u0627\u064f\u0631\u062f\u0648'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', '\xe8d\xe8 Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')])),
                ('editors', models.ManyToManyField(related_name='locales_editor', to=settings.AUTH_USER_MODEL, blank=True)),
                ('leaders', models.ManyToManyField(related_name='locales_leader', to=settings.AUTH_USER_MODEL, blank=True)),
                ('reviewers', models.ManyToManyField(related_name='locales_reviewer', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['locale'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Revision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('summary', models.TextField()),
                ('content', models.TextField()),
                ('keywords', models.CharField(max_length=255, blank=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('reviewed', models.DateTimeField(null=True)),
                ('expires', models.DateTimeField(null=True, blank=True)),
                ('significance', models.IntegerField(null=True, choices=[(10, "Minor details that don't affect the instructions"), (20, "Content changes that don't require immediate translation"), (30, 'Major content changes that will make older translations inaccurate')])),
                ('comment', models.CharField(max_length=255)),
                ('is_approved', models.BooleanField(default=False, db_index=True)),
                ('is_ready_for_localization', models.BooleanField(default=False)),
                ('readied_for_localization', models.DateTimeField(null=True)),
                ('based_on', models.ForeignKey(blank=True, to='wiki.Revision', null=True)),
                ('creator', models.ForeignKey(related_name='created_revisions', to=settings.AUTH_USER_MODEL)),
                ('document', models.ForeignKey(related_name='revisions', to='wiki.Document')),
                ('readied_for_localization_by', models.ForeignKey(related_name='readied_for_l10n_revisions', to=settings.AUTH_USER_MODEL, null=True)),
                ('reviewer', models.ForeignKey(related_name='reviewed_revisions', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'permissions': [('review_revision', 'Can review a revision'), ('mark_ready_for_l10n', 'Can mark revision as ready for localization'), ('edit_keywords', 'Can edit keywords')],
            },
            bases=(models.Model, kitsune.search.models.SearchMixin),
        ),
        migrations.AddField(
            model_name='helpfulvote',
            name='revision',
            field=models.ForeignKey(related_name='poll_votes', to='wiki.Revision'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='documentlink',
            unique_together={('linked_from', 'linked_to', 'kind')},
        ),
        migrations.AlterUniqueTogether(
            name='documentimage',
            unique_together={('document', 'image')},
        ),
        migrations.AddField(
            model_name='document',
            name='current_revision',
            field=models.ForeignKey(related_name='current_for+', to='wiki.Revision', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='latest_localizable_revision',
            field=models.ForeignKey(related_name='localizable_for+', to='wiki.Revision', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='parent',
            field=models.ForeignKey(related_name='translations', blank=True, to='wiki.Document', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='products',
            field=models.ManyToManyField(to='products.Product'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='tags',
            field=kitsune.tags.models.BigVocabTaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='topics',
            field=models.ManyToManyField(to='products.Topic'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together={('title', 'locale'), ('parent', 'locale'), ('slug', 'locale')},
        ),
    ]
