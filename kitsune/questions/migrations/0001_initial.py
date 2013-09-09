# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Question'
        db.create_table('questions_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='questions', to=orm['auth.User'])),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('updated_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='questions_updated', null=True, to=orm['auth.User'])),
            ('last_answer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='last_reply_in', null=True, to=orm['questions.Answer'])),
            ('num_answers', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('solution', self.gf('django.db.models.fields.related.ForeignKey')(related_name='solution_for', null=True, to=orm['questions.Answer'])),
            ('is_locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('num_votes_past_week', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, db_index=True)),
            ('locale', self.gf('kitsune.sumo.models.LocaleField')(default='en-US', max_length=7)),
        ))
        db.send_create_signal('questions', ['Question'])

        # Adding M2M table for field products on 'Question'
        m2m_table_name = db.shorten_name('questions_question_products')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('question', models.ForeignKey(orm['questions.question'], null=False)),
            ('product', models.ForeignKey(orm['products.product'], null=False))
        ))
        db.create_unique(m2m_table_name, ['question_id', 'product_id'])

        # Adding M2M table for field topics on 'Question'
        m2m_table_name = db.shorten_name('questions_question_topics')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('question', models.ForeignKey(orm['questions.question'], null=False)),
            ('topic', models.ForeignKey(orm['products.topic'], null=False))
        ))
        db.create_unique(m2m_table_name, ['question_id', 'topic_id'])

        # Adding model 'QuestionMetaData'
        db.create_table('questions_questionmetadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='metadata_set', to=orm['questions.Question'])),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('questions', ['QuestionMetaData'])

        # Adding unique constraint on 'QuestionMetaData', fields ['question', 'name']
        db.create_unique('questions_questionmetadata', ['question_id', 'name'])

        # Adding model 'QuestionVisits'
        db.create_table('questions_questionvisits', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Question'], unique=True)),
            ('visits', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
        ))
        db.send_create_signal('questions', ['QuestionVisits'])

        # Adding model 'Answer'
        db.create_table('questions_answer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='answers', to=orm['questions.Question'])),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='answers', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('updated_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='answers_updated', null=True, to=orm['auth.User'])),
            ('page', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('questions', ['Answer'])

        # Adding model 'QuestionVote'
        db.create_table('questions_questionvote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='votes', to=orm['questions.Question'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='question_votes', null=True, to=orm['auth.User'])),
            ('anonymous_id', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
        ))
        db.send_create_signal('questions', ['QuestionVote'])

        # Adding model 'AnswerVote'
        db.create_table('questions_answervote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('answer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='votes', to=orm['questions.Answer'])),
            ('helpful', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='answer_votes', null=True, to=orm['auth.User'])),
            ('anonymous_id', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
        ))
        db.send_create_signal('questions', ['AnswerVote'])

        # Adding model 'VoteMetadata'
        db.create_table('questions_votemetadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal('questions', ['VoteMetadata'])


    def backwards(self, orm):
        # Removing unique constraint on 'QuestionMetaData', fields ['question', 'name']
        db.delete_unique('questions_questionmetadata', ['question_id', 'name'])

        # Deleting model 'Question'
        db.delete_table('questions_question')

        # Removing M2M table for field products on 'Question'
        db.delete_table(db.shorten_name('questions_question_products'))

        # Removing M2M table for field topics on 'Question'
        db.delete_table(db.shorten_name('questions_question_topics'))

        # Deleting model 'QuestionMetaData'
        db.delete_table('questions_questionmetadata')

        # Deleting model 'QuestionVisits'
        db.delete_table('questions_questionvisits')

        # Deleting model 'Answer'
        db.delete_table('questions_answer')

        # Deleting model 'QuestionVote'
        db.delete_table('questions_questionvote')

        # Deleting model 'AnswerVote'
        db.delete_table('questions_answervote')

        # Deleting model 'VoteMetadata'
        db.delete_table('questions_votemetadata')


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
        'flagit.flaggedobject': {
            'Meta': {'ordering': "['created']", 'unique_together': "(('content_type', 'object_id', 'creator'),)", 'object_name': 'FlaggedObject'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flags'", 'to': "orm['auth.User']"}),
            'handled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'handled_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
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
        'questions.answer': {
            'Meta': {'ordering': "['created']", 'object_name': 'Answer'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answers'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answers'", 'to': "orm['questions.Question']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answers_updated'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'questions.answervote': {
            'Meta': {'object_name': 'AnswerVote'},
            'anonymous_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['questions.Answer']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answer_votes'", 'null': 'True', 'to': "orm['auth.User']"}),
            'helpful': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'questions.question': {
            'Meta': {'ordering': "['-updated']", 'object_name': 'Question'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'questions'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_answer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_reply_in'", 'null': 'True', 'to': "orm['questions.Answer']"}),
            'locale': ('kitsune.sumo.models.LocaleField', [], {'default': "'en-US'", 'max_length': '7'}),
            'num_answers': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'num_votes_past_week': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['products.Product']", 'symmetrical': 'False'}),
            'solution': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'solution_for'", 'null': 'True', 'to': "orm['questions.Answer']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'topics': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['products.Topic']", 'symmetrical': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'questions_updated'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'questions.questionmetadata': {
            'Meta': {'unique_together': "(('question', 'name'),)", 'object_name': 'QuestionMetaData'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'metadata_set'", 'to': "orm['questions.Question']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'questions.questionvisits': {
            'Meta': {'object_name': 'QuestionVisits'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['questions.Question']", 'unique': 'True'}),
            'visits': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        'questions.questionvote': {
            'Meta': {'object_name': 'QuestionVote'},
            'anonymous_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_votes'", 'null': 'True', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['questions.Question']"})
        },
        'questions.votemetadata': {
            'Meta': {'object_name': 'VoteMetadata'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
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
        'upload.imageattachment': {
            'Meta': {'object_name': 'ImageAttachment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'image_attachments'", 'to': "orm['auth.User']"}),
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'})
        }
    }

    complete_apps = ['questions']