# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Image'
        db.create_table('gallery_image', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('updated_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=10000)),
            ('locale', self.gf('kitsune.sumo.models.LocaleField')(default='en-US', max_length=7, db_index=True)),
            ('is_draft', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='gallery_images', to=orm['auth.User'])),
            ('file', self.gf('django.db.models.fields.files.ImageField')(max_length=250)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=250, null=True)),
        ))
        db.send_create_signal('gallery', ['Image'])

        # Adding unique constraint on 'Image', fields ['locale', 'title']
        db.create_unique('gallery_image', ['locale', 'title'])

        # Adding unique constraint on 'Image', fields ['is_draft', 'creator']
        db.create_unique('gallery_image', ['is_draft', 'creator_id'])

        # Adding model 'Video'
        db.create_table('gallery_video', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('updated_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=10000)),
            ('locale', self.gf('kitsune.sumo.models.LocaleField')(default='en-US', max_length=7, db_index=True)),
            ('is_draft', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='gallery_videos', to=orm['auth.User'])),
            ('webm', self.gf('django.db.models.fields.files.FileField')(max_length=250, null=True)),
            ('ogv', self.gf('django.db.models.fields.files.FileField')(max_length=250, null=True)),
            ('flv', self.gf('django.db.models.fields.files.FileField')(max_length=250, null=True)),
            ('poster', self.gf('django.db.models.fields.files.ImageField')(max_length=250, null=True)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=250, null=True)),
        ))
        db.send_create_signal('gallery', ['Video'])

        # Adding unique constraint on 'Video', fields ['locale', 'title']
        db.create_unique('gallery_video', ['locale', 'title'])

        # Adding unique constraint on 'Video', fields ['is_draft', 'creator']
        db.create_unique('gallery_video', ['is_draft', 'creator_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Video', fields ['is_draft', 'creator']
        db.delete_unique('gallery_video', ['is_draft', 'creator_id'])

        # Removing unique constraint on 'Video', fields ['locale', 'title']
        db.delete_unique('gallery_video', ['locale', 'title'])

        # Removing unique constraint on 'Image', fields ['is_draft', 'creator']
        db.delete_unique('gallery_image', ['is_draft', 'creator_id'])

        # Removing unique constraint on 'Image', fields ['locale', 'title']
        db.delete_unique('gallery_image', ['locale', 'title'])

        # Deleting model 'Image'
        db.delete_table('gallery_image')

        # Deleting model 'Video'
        db.delete_table('gallery_video')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'gallery.image': {
            'Meta': {'ordering': "['-created']", 'unique_together': "(('locale', 'title'), ('is_draft', 'creator'))", 'object_name': 'Image'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'gallery_images'", 'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '10000'}),
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_draft': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'locale': ('kitsune.sumo.models.LocaleField', [], {'default': "'en-US'", 'max_length': '7', 'db_index': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '250', 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'gallery.video': {
            'Meta': {'ordering': "['-created']", 'unique_together': "(('locale', 'title'), ('is_draft', 'creator'))", 'object_name': 'Video'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'gallery_videos'", 'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '10000'}),
            'flv': ('django.db.models.fields.files.FileField', [], {'max_length': '250', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_draft': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'locale': ('kitsune.sumo.models.LocaleField', [], {'default': "'en-US'", 'max_length': '7', 'db_index': 'True'}),
            'ogv': ('django.db.models.fields.files.FileField', [], {'max_length': '250', 'null': 'True'}),
            'poster': ('django.db.models.fields.files.ImageField', [], {'max_length': '250', 'null': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '250', 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'webm': ('django.db.models.fields.files.FileField', [], {'max_length': '250', 'null': 'True'})
        }
    }

    complete_apps = ['gallery']