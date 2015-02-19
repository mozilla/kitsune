# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Product.sprite_height'
        db.add_column(u'products_product', 'sprite_height',
                      self.gf('django.db.models.fields.IntegerField')(default=None, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Product.sprite_height'
        db.delete_column(u'products_product', 'sprite_height')


    models = {
        u'products.platform': {
            'Meta': {'object_name': 'Platform'},
            'display_order': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'products.product': {
            'Meta': {'ordering': "['display_order']", 'object_name': 'Product'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_order': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'image_cachebuster': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '32', 'null': 'True'}),
            'image_offset': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'platforms': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['products.Platform']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'sprite_height': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'products.topic': {
            'Meta': {'ordering': "['product', 'display_order']", 'unique_together': "(('slug', 'product'),)", 'object_name': 'Topic'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_order': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subtopics'", 'null': 'True', 'to': u"orm['products.Topic']"}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics'", 'to': u"orm['products.Product']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'products.version': {
            'Meta': {'ordering': "['-max_version']", 'object_name': 'Version'},
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_version': ('django.db.models.fields.FloatField', [], {}),
            'min_version': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['products.Product']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['products']