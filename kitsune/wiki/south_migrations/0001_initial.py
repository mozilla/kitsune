# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Document'
        db.create_table('wiki_document', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('is_template', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('is_localizable', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('locale', self.gf('kitsune.sumo.models.LocaleField')(default='en-US', max_length=7, db_index=True)),
            ('current_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='current_for+', null=True, to=orm['wiki.Revision'])),
            ('latest_localizable_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='localizable_for+', null=True, to=orm['wiki.Revision'])),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='translations', null=True, to=orm['wiki.Document'])),
            ('html', self.gf('django.db.models.fields.TextField')()),
            ('category', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('is_archived', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('allow_discussion', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('needs_change', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('needs_change_comment', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
        ))
        db.send_create_signal('wiki', ['Document'])

        # Adding unique constraint on 'Document', fields ['parent', 'locale']
        db.create_unique('wiki_document', ['parent_id', 'locale'])

        # Adding unique constraint on 'Document', fields ['title', 'locale']
        db.create_unique('wiki_document', ['title', 'locale'])

        # Adding unique constraint on 'Document', fields ['slug', 'locale']
        db.create_unique('wiki_document', ['slug', 'locale'])

        # Adding M2M table for field contributors on 'Document'
        m2m_table_name = db.shorten_name('wiki_document_contributors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('document', models.ForeignKey(orm['wiki.document'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['document_id', 'user_id'])

        # Adding M2M table for field products on 'Document'
        m2m_table_name = db.shorten_name('wiki_document_products')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('document', models.ForeignKey(orm['wiki.document'], null=False)),
            ('product', models.ForeignKey(orm['products.product'], null=False))
        ))
        db.create_unique(m2m_table_name, ['document_id', 'product_id'])

        # Adding M2M table for field topics on 'Document'
        m2m_table_name = db.shorten_name('wiki_document_topics')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('document', models.ForeignKey(orm['wiki.document'], null=False)),
            ('topic', models.ForeignKey(orm['products.topic'], null=False))
        ))
        db.create_unique(m2m_table_name, ['document_id', 'topic_id'])

        # Adding model 'Revision'
        db.create_table('wiki_revision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['wiki.Document'])),
            ('summary', self.gf('django.db.models.fields.TextField')()),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('keywords', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('reviewed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('significance', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('reviewer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reviewed_revisions', null=True, to=orm['auth.User'])),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_revisions', to=orm['auth.User'])),
            ('is_approved', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('based_on', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wiki.Revision'], null=True, blank=True)),
            ('is_ready_for_localization', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('readied_for_localization', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('readied_for_localization_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='readied_for_l10n_revisions', null=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('wiki', ['Revision'])

        # Adding model 'HelpfulVote'
        db.create_table('wiki_helpfulvote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='poll_votes', to=orm['wiki.Revision'])),
            ('helpful', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='poll_votes', null=True, to=orm['auth.User'])),
            ('anonymous_id', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('user_agent', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal('wiki', ['HelpfulVote'])

        # Adding model 'HelpfulVoteMetadata'
        db.create_table('wiki_helpfulvotemetadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vote', self.gf('django.db.models.fields.related.ForeignKey')(related_name='metadata', to=orm['wiki.HelpfulVote'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal('wiki', ['HelpfulVoteMetadata'])

        # Adding model 'ImportantDate'
        db.create_table('wiki_importantdate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('date', self.gf('django.db.models.fields.DateField')(db_index=True)),
        ))
        db.send_create_signal('wiki', ['ImportantDate'])

        # Adding model 'Locale'
        db.create_table('wiki_locale', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('locale', self.gf('django.db.models.fields.CharField')(max_length=7, db_index=True)),
        ))
        db.send_create_signal('wiki', ['Locale'])

        # Adding M2M table for field leaders on 'Locale'
        m2m_table_name = db.shorten_name('wiki_locale_leaders')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('locale', models.ForeignKey(orm['wiki.locale'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['locale_id', 'user_id'])

        # Adding M2M table for field reviewers on 'Locale'
        m2m_table_name = db.shorten_name('wiki_locale_reviewers')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('locale', models.ForeignKey(orm['wiki.locale'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['locale_id', 'user_id'])

        # Adding M2M table for field editors on 'Locale'
        m2m_table_name = db.shorten_name('wiki_locale_editors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('locale', models.ForeignKey(orm['wiki.locale'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['locale_id', 'user_id'])

        # Adding model 'DocumentLink'
        db.create_table('wiki_documentlink', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('linked_to', self.gf('django.db.models.fields.related.ForeignKey')(related_name='documentlink_from_set', to=orm['wiki.Document'])),
            ('linked_from', self.gf('django.db.models.fields.related.ForeignKey')(related_name='documentlink_to_set', to=orm['wiki.Document'])),
            ('kind', self.gf('django.db.models.fields.CharField')(max_length=16)),
        ))
        db.send_create_signal('wiki', ['DocumentLink'])

        # Adding unique constraint on 'DocumentLink', fields ['linked_from', 'linked_to']
        db.create_unique('wiki_documentlink', ['linked_from_id', 'linked_to_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'DocumentLink', fields ['linked_from', 'linked_to']
        db.delete_unique('wiki_documentlink', ['linked_from_id', 'linked_to_id'])

        # Removing unique constraint on 'Document', fields ['slug', 'locale']
        db.delete_unique('wiki_document', ['slug', 'locale'])

        # Removing unique constraint on 'Document', fields ['title', 'locale']
        db.delete_unique('wiki_document', ['title', 'locale'])

        # Removing unique constraint on 'Document', fields ['parent', 'locale']
        db.delete_unique('wiki_document', ['parent_id', 'locale'])

        # Deleting model 'Document'
        db.delete_table('wiki_document')

        # Removing M2M table for field contributors on 'Document'
        db.delete_table(db.shorten_name('wiki_document_contributors'))

        # Removing M2M table for field products on 'Document'
        db.delete_table(db.shorten_name('wiki_document_products'))

        # Removing M2M table for field topics on 'Document'
        db.delete_table(db.shorten_name('wiki_document_topics'))

        # Deleting model 'Revision'
        db.delete_table('wiki_revision')

        # Deleting model 'HelpfulVote'
        db.delete_table('wiki_helpfulvote')

        # Deleting model 'HelpfulVoteMetadata'
        db.delete_table('wiki_helpfulvotemetadata')

        # Deleting model 'ImportantDate'
        db.delete_table('wiki_importantdate')

        # Deleting model 'Locale'
        db.delete_table('wiki_locale')

        # Removing M2M table for field leaders on 'Locale'
        db.delete_table(db.shorten_name('wiki_locale_leaders'))

        # Removing M2M table for field reviewers on 'Locale'
        db.delete_table(db.shorten_name('wiki_locale_reviewers'))

        # Removing M2M table for field editors on 'Locale'
        db.delete_table(db.shorten_name('wiki_locale_editors'))

        # Deleting model 'DocumentLink'
        db.delete_table('wiki_documentlink')


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
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        },
        'tidings.watch': {
            'Meta': {'object_name': 'Watch'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'wiki.document': {
            'Meta': {'unique_together': "(('parent', 'locale'), ('title', 'locale'), ('slug', 'locale'))", 'object_name': 'Document'},
            'allow_discussion': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'category': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'contributors': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'}),
            'current_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'current_for+'", 'null': 'True', 'to': "orm['wiki.Revision']"}),
            'html': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'is_localizable': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_template': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'latest_localizable_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'localizable_for+'", 'null': 'True', 'to': "orm['wiki.Revision']"}),
            'locale': ('kitsune.sumo.models.LocaleField', [], {'default': "'en-US'", 'max_length': '7', 'db_index': 'True'}),
            'needs_change': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'needs_change_comment': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'translations'", 'null': 'True', 'to': "orm['wiki.Document']"}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['products.Product']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'topics': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['products.Topic']", 'symmetrical': 'False'})
        },
        'wiki.documentlink': {
            'Meta': {'unique_together': "(('linked_from', 'linked_to'),)", 'object_name': 'DocumentLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'linked_from': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documentlink_to_set'", 'to': "orm['wiki.Document']"}),
            'linked_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documentlink_from_set'", 'to': "orm['wiki.Document']"})
        },
        'wiki.helpfulvote': {
            'Meta': {'object_name': 'HelpfulVote'},
            'anonymous_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'poll_votes'", 'null': 'True', 'to': "orm['auth.User']"}),
            'helpful': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'poll_votes'", 'to': "orm['wiki.Revision']"}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        'wiki.helpfulvotemetadata': {
            'Meta': {'object_name': 'HelpfulVoteMetadata'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'vote': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'metadata'", 'to': "orm['wiki.HelpfulVote']"})
        },
        'wiki.importantdate': {
            'Meta': {'object_name': 'ImportantDate'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'wiki.locale': {
            'Meta': {'ordering': "['locale']", 'object_name': 'Locale'},
            'editors': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'locales_editor'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'leaders': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'locales_leader'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '7', 'db_index': 'True'}),
            'reviewers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'locales_reviewer'", 'blank': 'True', 'to': "orm['auth.User']"})
        },
        'wiki.revision': {
            'Meta': {'object_name': 'Revision'},
            'based_on': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.Revision']", 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_revisions'", 'to': "orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['wiki.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'is_ready_for_localization': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'readied_for_localization': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'readied_for_localization_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'readied_for_l10n_revisions'", 'null': 'True', 'to': "orm['auth.User']"}),
            'reviewed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviewed_revisions'", 'null': 'True', 'to': "orm['auth.User']"}),
            'significance': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['wiki']