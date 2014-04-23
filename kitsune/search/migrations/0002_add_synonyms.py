# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Synonym'
        db.create_table(u'search_synonym', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('from_words', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('to_words', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'search', ['Synonym'])


    def backwards(self, orm):
        # Deleting model 'Synonym'
        db.delete_table(u'search_synonym')


    models = {
        u'search.record': {
            'Meta': {'object_name': 'Record'},
            'endtime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'starttime': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'search.synonym': {
            'Meta': {'object_name': 'Synonym'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'from_words': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_words': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['search']