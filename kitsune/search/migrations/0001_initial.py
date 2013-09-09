# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Record'
        db.create_table('search_record', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('starttime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('endtime', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('search', ['Record'])


    def backwards(self, orm):
        # Deleting model 'Record'
        db.delete_table('search_record')


    models = {
        'search.record': {
            'Meta': {'object_name': 'Record'},
            'endtime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'starttime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['search']