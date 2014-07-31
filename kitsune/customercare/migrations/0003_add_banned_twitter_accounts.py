# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        # Pulled from settings.py on 07/31/14
        users_to_ban = [
            'lucasbytegenius',
            'sandeep81910240',
            'balapandu222',
            'Pedro2993919',
            'mali_krishna',
            'The_911_waw',
        ]

        existing_users = (orm.TwitterAccount.objects
                          .filter(username__in=users_to_ban).all())
        existing_usernames = [account.username for account in existing_users]
        non_existing_users = [user for user in users_to_ban
                              if user not in existing_usernames]

        for user in existing_users:
            user.banned = True
            user.save()

        for username in non_existing_users:
            banned_user = orm.TwitterAccount(username=username, banned=True)
            banned_user.save()

    def backwards(self, orm):
        # Pulled from settings.py on 07/31/14
        users_to_unban = [
            'lucasbytegenius',
            'sandeep81910240',
            'balapandu222',
            'Pedro2993919',
            'mali_krishna',
            'The_911_waw',
        ]
        users = (orm.TwitterAccount.objects
                 .filter(username__in=users_to_unban).all())
        for user in users:
            user.banned = False
            user.save()

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'customercare.reply': {
            'Meta': {'object_name': 'Reply'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'raw_json': ('django.db.models.fields.TextField', [], {}),
            'reply_to_tweet_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'tweet_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'twitter_username': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'tweet_replies'", 'null': 'True', 'to': u"orm['auth.User']"})
        },
        u'customercare.tweet': {
            'Meta': {'ordering': "('-tweet_id',)", 'object_name': 'Tweet'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'raw_json': ('django.db.models.fields.TextField', [], {}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'replies'", 'null': 'True', 'to': u"orm['customercare.Tweet']"}),
            'tweet_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'})
        },
        u'customercare.twitteraccount': {
            'Meta': {'object_name': 'TwitterAccount'},
            'banned': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        }
    }

    complete_apps = ['customercare']
    symmetrical = True
