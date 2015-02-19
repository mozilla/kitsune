# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Record'
        db.create_table(u'journal_record', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('level', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('src', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('msg', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'journal', ['Record'])


    def backwards(self, orm):
        # Deleting model 'Record'
        db.delete_table(u'journal_record')


    models = {
        u'journal.record': {
            'Meta': {'object_name': 'Record'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'msg': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'src': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['journal']