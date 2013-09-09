# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Product'
        db.create_table('products_product', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=250, null=True, blank=True)),
            ('display_order', self.gf('django.db.models.fields.IntegerField')()),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('products', ['Product'])

        # Adding model 'Topic'
        db.create_table('products_topic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=250, null=True, blank=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='topics', to=orm['products.Product'])),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='subtopics', null=True, to=orm['products.Topic'])),
            ('display_order', self.gf('django.db.models.fields.IntegerField')()),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('products', ['Topic'])

        # Adding unique constraint on 'Topic', fields ['slug', 'product']
        db.create_unique('products_topic', ['slug', 'product_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Topic', fields ['slug', 'product']
        db.delete_unique('products_topic', ['slug', 'product_id'])

        # Deleting model 'Product'
        db.delete_table('products_product')

        # Deleting model 'Topic'
        db.delete_table('products_topic')


    models = {
        'products.product': {
            'Meta': {'ordering': "['display_order']", 'object_name': 'Product'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_order': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'products.topic': {
            'Meta': {'ordering': "['product', 'display_order']", 'unique_together': "(('slug', 'product'),)", 'object_name': 'Topic'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_order': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subtopics'", 'null': 'True', 'to': "orm['products.Topic']"}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics'", 'to': "orm['products.Product']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['products']