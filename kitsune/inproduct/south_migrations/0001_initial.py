# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Redirect'
        db.create_table('inproduct_redirect', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=30, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=30, blank=True)),
            ('platform', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=30, blank=True)),
            ('locale', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=10, blank=True)),
            ('topic', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=50, blank=True)),
            ('target', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('inproduct', ['Redirect'])

        # Adding unique constraint on 'Redirect', fields ['product', 'version', 'platform', 'locale', 'topic']
        db.create_unique('inproduct_redirect', ['product', 'version', 'platform', 'locale', 'topic'])


    def backwards(self, orm):
        # Removing unique constraint on 'Redirect', fields ['product', 'version', 'platform', 'locale', 'topic']
        db.delete_unique('inproduct_redirect', ['product', 'version', 'platform', 'locale', 'topic'])

        # Deleting model 'Redirect'
        db.delete_table('inproduct_redirect')


    models = {
        'inproduct.redirect': {
            'Meta': {'unique_together': "(('product', 'version', 'platform', 'locale', 'topic'),)", 'object_name': 'Redirect'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '10', 'blank': 'True'}),
            'platform': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'}),
            'product': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'topic': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'blank': 'True'})
        }
    }

    complete_apps = ['inproduct']