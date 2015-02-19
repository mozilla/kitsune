# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Q

from south.v2 import DataMigration

from kitsune.questions.models import QuestionMappingType
from kitsune.search.es_utils import ES_EXCEPTIONS, get_documents
from kitsune.search.tasks import index_task
from kitsune.sumo.utils import chunked


class Migration(DataMigration):

    def change_and_reindex(self, orm, is_archived, is_locked):
        """Locks all questions that were created over 180 days ago"""
        # Get a list of ids of questions we're going to go change. We need
        # a list of ids so that we can feed it to the update, but then
        # also know what we need to update in the index.
        days_180 = datetime.now() - timedelta(days=180)
        assert is_archived != is_locked
        f = Q(created__lte=days_180)
        if is_archived:
            f |= Q(is_locked=True)
        if is_locked:
            f |= Q(is_archived=True)

        # Update the DB
        (orm.Question.objects.filter(f)
            .update(is_archived=is_archived, is_locked=is_locked))

        # Using the efficient .update() of query sets doesn't emit any
        # signals, so live indexing won't automatically happen. This
        # does it manually.
        if settings.ES_LIVE_INDEXING:
            q_ids = list(orm.Question.objects.filter(f)
                         .values_list('id', flat=True))
            try:
                # This is going to process about 200K questions in
                # production, so it will take a while and stress
                # everything. To alleviate this stress, it is
                # divided into chunks.

                for chunk in chunked(q_ids, 1000):
                    # Fetch all the documents we need to update.
                    es_docs = get_documents(QuestionMappingType, chunk)

                    documents = []

                    # For each document, update the data and stick it
                    # back in the index.
                    for doc in es_docs:
                        doc[u'question_is_locked'] = is_locked
                        doc[u'question_is_archived'] = is_archived
                        doc[u'indexed_on'] = int(time.time())
                        documents.append(doc)

                    if documents:
                        QuestionMappingType.bulk_index(documents)

            except ES_EXCEPTIONS:
                # Something happened with ES, so let's push index
                # updating into an index_task which retries when it
                # fails because of ES issues.
                index_task.delay(QuestionMappingType, q_ids)

    def forwards(self, orm):
        """Archives old questions that were previously locked."""
        self.change_and_reindex(orm, True, False)

    def backwards(self, orm):
        """Locks any questions that are archived."""
        self.change_and_reindex(orm, False, True)


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
            'is_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
    symmetrical = True
