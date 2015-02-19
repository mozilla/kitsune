# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models


class Migration(DataMigration):

    def forwards(self, orm):
        """Add platforms and versions."""

        def platform(name, slug, order):
            p = orm.Platform(name=name, slug=slug, display_order=order,
                             visible=True)
            p.save()
            return p

        # Platforms
        win8 = platform('Windows 8', 'win8', 6)
        win7 = platform('Windows 7/Vista', 'win7', 5)
        winxp = platform('Windows XP', 'winxp', 4)
        mac = platform('Mac', 'mac', 3)
        linux = platform('Linux', 'linux', 2)
        android = platform('Android', 'android', 1)
        # "The web is the platform". This is for things like FxOS and Webmaker 
        web = platform('Web', 'web', 0)

        # Assign platforms to products.
        platform_product_map = {
            'firefox': [winxp, win7, win8, mac, linux],
            'mobile': [android],
            'firefox-os': [web],
            'marketplace': [web],
            'webmaker': [web],
            'persona': [web],
        }
        for slug, platforms in platform_product_map.items():
            try:
                product = orm.Product.objects.get(slug=slug)
                for platform in platforms:
                    product.platforms.add(platform)
            except orm.Product.DoesNotExist:
                # If we don't have the product, (such as because this is
                # migrating using a non-prod db), just skip it.
                pass

        # Make some versions.
        def version_for_slug(slug, version):
            try:
                product = orm.Product.objects.get(slug=slug)
                orm.Version(product=product, **version).save()
            except orm.Product.DoesNotExist:
                pass


        # Go all the way to version 35 as a workaround for deprecating
        # {for fx35} support. This will make the old tags hidden for a
        # while, until Firefox 35 comes out. We should have the articles
        # fixed by then.
        for i in range(4, 35):
            name = 'Version %d' % i
            if i in [10, 17]:
                name = 'Version %d (ESR)' % i

            version_for_slug('firefox', {
                'name': name,
                'slug': 'fx%d' % i,
                'min_version': i,
                'max_version': i + 1,
                'default': i == 25,
                'visible': i in range(23, 27) or i == 17,
            })

        for i in range(4, 35):
            # No Firefox 13 for Android.
            if i == 13:
                continue

            version_for_slug('mobile', {
                'name': 'Version %d' % i, 
                'slug': 'm%d' % i,
                'min_version': i,
                'max_version': i + 1,
                'default': i == 24,
                'visible': i in range(23, 27),
            })

        for i in [1.0, 1.1, 1.2, 1.3]:
            version_for_slug('firefox-os', {
                'name': 'Version %0.1f' % i,
                'slug': 'fxos%0.1f' % i,
                'min_version': i,
                'max_version': i + 0.1,
                'default': i == 1.1,
                'visible': True,
            })

        versionless_products = [
            ('Marketplace', 'marketplace'),
            ('Webmaker', 'webmaker'),
            ('Persona', 'persona'),
        ]
        for name, slug in versionless_products:
            version_for_slug(slug, {
                'name': name,
                'slug': slug,
                'min_version': 0,
                'max_version': 0,
                'default': True,
                'visible': True,
            })

    def backwards(self, orm):
        "Write your backwards methods here."
        orm.Platform.objects.all().delete()
        orm.Version.objects.all().delete()

    models = {
        'products.platform': {
            'Meta': {'object_name': 'Platform'},
            'display_order': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'products.product': {
            'Meta': {'ordering': "['display_order']", 'object_name': 'Product'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_order': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'platforms': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['products.Platform']", 'symmetrical': 'False'}),
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
        },
        'products.version': {
            'Meta': {'ordering': "['-max_version']", 'object_name': 'Version'},
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_version': ('django.db.models.fields.FloatField', [], {}),
            'min_version': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': "orm['products.Product']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['products']
    symmetrical = True
