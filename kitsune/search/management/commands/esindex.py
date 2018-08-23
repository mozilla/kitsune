import datetime
import logging

from celery import chord, chain
from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from django_elasticsearch_dsl.registries import registry

from kitsune.search import config
from ...tasks import (index_objects_to_es, switch_es_index, create_new_es_index,
                      index_missing_objects)
from ...utils import chunk_queryset

log = logging.getLogger(__name__)


class Command(BaseCommand):

    @staticmethod
    def _get_indexing_tasks(app_label, model_name, queryset, document_class, index_name):
        queryset = queryset.values_list('id', flat=True)
        chunked_queryset = chunk_queryset(queryset, settings.ES_TASK_CHUNK_SIZE)

        for chunk in chunked_queryset:
            data = {
                'app_label': app_label,
                'model_name': model_name,
                'document_class': document_class,
                'index_name': index_name,
                'objects_id': list(chunk)
            }
            yield index_objects_to_es.si(**data)

    def _run_reindex_tasks(self, es_document, queryset, index_time, locale=None, suffix=None):

        task_kwargs = {
            'app_label': queryset.model._meta.app_label,
            'model_name': queryset.model.__name__,
            'document_class': str(es_document)
        }
        index_alias = es_document._doc_type.index
        new_index_name = "{}_{}".format(index_alias, index_time.strftime('%Y%m%d%H%M%S'))

        if suffix:
            new_index_name = "{}_{}".format(new_index_name, suffix)

            index_alias_format = config.INDEX_ALIAS_FORMAT
            index_alias = index_alias_format.format(index_name=index_alias,
                                                    suffix=suffix)

        pre_index_task = create_new_es_index.si(new_index_name=new_index_name,
                                             locale=locale, **task_kwargs)

        indexing_tasks = self._get_indexing_tasks(queryset=queryset,
                                                  index_name=new_index_name, **task_kwargs)

        post_index_task = switch_es_index.si(index_alias=index_alias,
                                             new_index_name=new_index_name, **task_kwargs)

        # Task to run in order to add the objects
        # that has been inserted into database while indexing_tasks was running
        # We pass the timestamp of indexing, so its possible to index later items
        # TODO: Find a better way so it can be generalized, not depend of timestamp
        missed_index_task = index_missing_objects.si(index_generation_time=index_time,
                                                     locale=locale, **task_kwargs)

        # http://celery.readthedocs.io/en/latest/userguide/canvas.html#chords
        chord_tasks = chord(header=list(indexing_tasks), body=post_index_task)
        # # http://celery.readthedocs.io/en/latest/userguide/canvas.html#chain
        chain(pre_index_task, chord_tasks, missed_index_task).apply_async()

        message = ("Successfully issued tasks for {} {}, total {} items"
                   .format(str(es_document), locale, queryset.count()))
        log.info(message)

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            dest='models',
            type=str,
            nargs='*',
            help=("Specify the model to be updated in elasticsearch."
                  "The format is <app_label>.<model_name>")
        )

    def handle(self, *args, **options):
        """
        Index models into Elasticsearch index asynchronously using celery.
        You can specify model to get indexed by passing
        `--model <app_label>.<model_name>` parameter.
        Otherwise, it will reindex all the models
        """
        models = None
        if options['models']:
            models = [apps.get_model(model_name) for model_name in options['models']]

        index_time = timezone.now()

        for doc in registry.get_documents(models):
            locales = getattr(doc, 'separate_index_locales', [])
            queryset = doc().get_queryset()

            # If the document need to have separate index for analyzer mapped locale,
            # we need to create different index with proper analyzer.
            if locales:
                for locale in locales:
                    # Check if any analyzer is mapped for the locale
                    if locale in settings.ES_LOCALE_ANALYZERS:
                        # Filter the queryset for that locale so only that
                        # locale object will be inside the index
                        # Also add a suffix that will be added
                        filtered_queryset = queryset.filter(locale=locale)
                        self._run_reindex_tasks(es_document=doc,
                                                queryset=filtered_queryset,
                                                index_time=index_time,
                                                locale=locale,
                                                suffix=locale.lower())

                # Create another index for other locales that does not have analyzer
                # So exclude the locale which have analyzer
                excluded_queryset = queryset.exclude(locale__in=locales)
                self._run_reindex_tasks(es_document=doc,
                                        queryset=excluded_queryset,
                                        index_time=index_time,
                                        suffix="general")

            else:
                self._run_reindex_tasks(es_document=doc, queryset=queryset, index_time=index_time)
