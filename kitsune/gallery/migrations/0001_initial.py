# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings
import kitsune.sumo.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('description', models.TextField(max_length=10000)),
                ('locale', kitsune.sumo.models.LocaleField(default=b'en-US', max_length=7, db_index=True, choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bg', '\u0411\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'bs', 'Bosanski'), (b'ca', 'catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'da', 'Dansk'), (b'de', 'Deutsch'), (b'ee', '\xc8\u028begbe'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English'), (b'es', 'Espa\xf1ol'), (b'et', 'eesti keel'), (b'eu', 'Euskara'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge (\xc9ire)'), (b'gl', 'Galego'), (b'gu-IN', '\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ac0'), (b'ha', '\u0647\u064e\u0631\u0652\u0634\u064e\u0646 \u0647\u064e\u0648\u0652\u0633\u064e'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'Magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'As\u1ee5s\u1ee5 Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'km', '\u1781\u17d2\u1798\u17c2\u179a'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'lt', 'lietuvi\u0173 kalba'), (b'ne-NP', '\u0928\u0947\u092a\u093e\u0932\u0940'), (b'nl', 'Nederlands'), (b'no', 'Norsk'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'si', '\u0dc3\u0dd2\u0d82\u0dc4\u0dbd'), (b'sk', 'sloven\u010dina'), (b'sl', 'sloven\u0161\u010dina'), (b'sq', 'Shqip'), (b'sr-Cyrl', '\u0421\u0440\u043f\u0441\u043a\u0438'), (b'sw', 'Kiswahili'), (b'sv', 'Svenska'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'ta-LK', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd (\u0b87\u0bb2\u0b99\u0bcd\u0b95\u0bc8)'), (b'te', '\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41'), (b'th', '\u0e44\u0e17\u0e22'), (b'tr', 'T\xfcrk\xe7e'), (b'uk', '\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430'), (b'ur', '\u0627\u064f\u0631\u062f\u0648'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', '\xe8d\xe8 Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')])),
                ('is_draft', models.NullBooleanField(default=None, editable=False)),
                ('file', models.ImageField(height_field=b'height', width_field=b'width', max_length=250, upload_to=b'uploads/gallery/images/')),
                ('thumbnail', models.ImageField(max_length=250, null=True, upload_to=b'uploads/gallery/images/thumbnails/')),
                ('height', models.IntegerField(null=True)),
                ('width', models.IntegerField(null=True)),
                ('creator', models.ForeignKey(related_name='gallery_images', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('updated', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('description', models.TextField(max_length=10000)),
                ('locale', kitsune.sumo.models.LocaleField(default=b'en-US', max_length=7, db_index=True, choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bg', '\u0411\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'bs', 'Bosanski'), (b'ca', 'catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'da', 'Dansk'), (b'de', 'Deutsch'), (b'ee', '\xc8\u028begbe'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English'), (b'es', 'Espa\xf1ol'), (b'et', 'eesti keel'), (b'eu', 'Euskara'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge (\xc9ire)'), (b'gl', 'Galego'), (b'gu-IN', '\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ac0'), (b'ha', '\u0647\u064e\u0631\u0652\u0634\u064e\u0646 \u0647\u064e\u0648\u0652\u0633\u064e'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'Magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'As\u1ee5s\u1ee5 Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'km', '\u1781\u17d2\u1798\u17c2\u179a'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'lt', 'lietuvi\u0173 kalba'), (b'ne-NP', '\u0928\u0947\u092a\u093e\u0932\u0940'), (b'nl', 'Nederlands'), (b'no', 'Norsk'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'si', '\u0dc3\u0dd2\u0d82\u0dc4\u0dbd'), (b'sk', 'sloven\u010dina'), (b'sl', 'sloven\u0161\u010dina'), (b'sq', 'Shqip'), (b'sr-Cyrl', '\u0421\u0440\u043f\u0441\u043a\u0438'), (b'sw', 'Kiswahili'), (b'sv', 'Svenska'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'ta-LK', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd (\u0b87\u0bb2\u0b99\u0bcd\u0b95\u0bc8)'), (b'te', '\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41'), (b'th', '\u0e44\u0e17\u0e22'), (b'tr', 'T\xfcrk\xe7e'), (b'uk', '\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430'), (b'ur', '\u0627\u064f\u0631\u062f\u0648'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', '\xe8d\xe8 Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')])),
                ('is_draft', models.NullBooleanField(default=None, editable=False)),
                ('webm', models.FileField(max_length=250, null=True, upload_to=b'uploads/gallery/videos/')),
                ('ogv', models.FileField(max_length=250, null=True, upload_to=b'uploads/gallery/videos/')),
                ('flv', models.FileField(max_length=250, null=True, upload_to=b'uploads/gallery/videos/')),
                ('poster', models.ImageField(max_length=250, null=True, upload_to=b'uploads/gallery/videos/thumbnails/')),
                ('thumbnail', models.ImageField(max_length=250, null=True, upload_to=b'uploads/gallery/videos/thumbnails/')),
                ('creator', models.ForeignKey(related_name='gallery_videos', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='video',
            unique_together={('is_draft', 'creator'), ('locale', 'title')},
        ),
        migrations.AlterUniqueTogether(
            name='image',
            unique_together={('is_draft', 'creator'), ('locale', 'title')},
        ),
    ]
