"""
Management command to set up E5 multilingual inference endpoint for semantic search.

This command helps configure the E5 multilingual model required for semantic_text fields.
"""

from django.core.management.base import BaseCommand, CommandError
from elasticsearch.exceptions import RequestError

from kitsune.search.es_utils import es_client
from kitsune.search.semantic_config import DEFAULT_EMBEDDING_MODEL, E5_MODELS


class Command(BaseCommand):
    help = 'Set up E5 multilingual inference endpoint for semantic search'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-id',
            type=str,
            default=DEFAULT_EMBEDDING_MODEL,
            choices=list(E5_MODELS.keys()),
            help=f'E5 model to use (default: {DEFAULT_EMBEDDING_MODEL})'
        )
        parser.add_argument(
            '--check-endpoint',
            action='store_true',
            help='Check if E5 inference endpoint is already configured'
        )
        parser.add_argument(
            '--num-allocations',
            type=int,
            default=1,
            help='Number of model allocations (default: 1)'
        )
        parser.add_argument(
            '--num-threads',
            type=int,
            default=1,
            help='Number of threads per allocation (default: 1)'
        )

    def handle(self, *args, **options):
        model_id = options['model_id']

        if options['check_endpoint']:
            self.check_e5_endpoint(model_id)
            return

        try:
            es = es_client()
            self.setup_e5_endpoint(
                es,
                model_id,
                options['num_allocations'],
                options['num_threads']
            )
        except Exception as e:
            raise CommandError(f"Failed to set up E5 endpoint: {e}")

    def check_e5_endpoint(self, model_id):
        """Check if E5 endpoint exists and is deployed."""
        try:
            es = es_client()

            # Check if model exists
            es.ml.get_trained_models(model_id=model_id)
            self.stdout.write(
                self.style.SUCCESS(f"E5 model '{model_id}' exists")
            )

            # Check if model is deployed
            stats = es.ml.get_trained_models_stats(model_id=model_id)
            deployment_stats = stats.get('trained_model_stats', [])

            if deployment_stats and len(deployment_stats) > 0:
                deployment_stats_info = deployment_stats[0].get('deployment_stats', {})
                deployment_state = deployment_stats_info.get('state', 'unknown')
                if deployment_state == 'started':
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"E5 model '{model_id}' is deployed and ready"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"E5 model '{model_id}' exists but is not started "
                            f"(state: {deployment_state})"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"E5 model '{model_id}' exists but is not deployed"
                    )
                )

            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"E5 model '{model_id}' not found or error occurred: {e}"
                )
            )
            return False

    def setup_e5_endpoint(self, es, model_id, num_allocations, num_threads):
        """Set up and deploy E5 multilingual model."""
        try:
            # First, check if the model already exists
            try:
                es.ml.get_trained_models(model_id=model_id)
                self.stdout.write(
                    self.style.WARNING(f"E5 model '{model_id}' already exists")
                )
            except RequestError:
                # Model doesn't exist, create it
                self.stdout.write(f"Creating E5 model '{model_id}'...")
                es.ml.put_trained_model(
                    model_id=model_id,
                    body={
                        "input": {"field_names": ["text_field"]},
                        "description": (
                            f"E5 multilingual model for semantic search: {model_id}"
                        )
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully created E5 model '{model_id}'"
                    )
                )

            # Deploy the model
            self.deploy_e5_model(es, model_id, num_allocations, num_threads)

        except RequestError as e:
            if "already exists" in str(e).lower():
                self.stdout.write(
                    self.style.WARNING(f"E5 model '{model_id}' already exists")
                )
                # Try to deploy it anyway
                self.deploy_e5_model(es, model_id, num_allocations, num_threads)
            else:
                raise CommandError(f"Failed to create E5 model: {e}")

    def deploy_e5_model(self, es, model_id, num_allocations, num_threads):
        """Deploy the E5 model for inference."""
        try:
            self.stdout.write(f"Deploying E5 model '{model_id}'...")
            es.ml.start_trained_model_deployment(
                model_id=model_id,
                body={
                    "number_of_allocations": num_allocations,
                    "threads_per_allocation": num_threads
                },
                wait_for="started",
                timeout="10m"
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deployed E5 model '{model_id}' "
                    f"with {num_allocations} allocation(s)"
                )
            )
        except RequestError as e:
            if "already started" in str(e).lower():
                self.stdout.write(
                    self.style.WARNING(f"E5 model '{model_id}' is already deployed")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to deploy E5 model: {e}")
                )
