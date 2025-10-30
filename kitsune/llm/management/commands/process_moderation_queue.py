from django.core.management.base import BaseCommand

from kitsune.llm.tasks import process_moderation_queue


class Command(BaseCommand):
    help = "Process stale flagged objects in the moderation queue through the LLM pipeline"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10,
            help="Number of items to process in this batch (default: 10)",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]

        self.stdout.write(
            f"Starting processing of stale moderation queue with batch size {batch_size}..."
        )

        process_moderation_queue(batch_size)
