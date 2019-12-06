from django.core.management.base import BaseCommand

from kitsune.search.v2.es7_utils import get_doc_types, index_object


class Command(BaseCommand):
    help = 'Reindex ES7 documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit', type=str, dest='limit', nargs='*', default='',
            help='Limit to specific doc types'
        )

    def handle(self, *args, **kwargs):
        doc_types = get_doc_types()

        limit = kwargs['limit']
        if limit:
            doc_types = [dt for dt in doc_types if dt.__name__ in limit]

        progress_msg = 'Indexed {progress} out of {count}'

        for dt in doc_types:
            self.stdout.write('Reindexing: {}'.format(dt.__name__))

            model = dt.get_model()
            qs = model.objects.all()
            progress = 0
            count = qs.count()

            for obj in qs:
                index_object.delay(dt.__name__, obj.id)

                progress += 1
                if progress % 100 == 0:
                    msg = progress_msg.format(progress=progress, count=count)
                    self.stdout.write(msg)
