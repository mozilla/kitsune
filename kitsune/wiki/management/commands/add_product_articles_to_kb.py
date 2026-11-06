from django.core.management.base import BaseCommand, CommandError

from kitsune.products.models import Product
from kitsune.wiki.config import DEFAULT_AUDIENCE_SLUG
from kitsune.wiki.models import Audience, Document


class Command(BaseCommand):
    help = "Adds a knowledge base to every original article of a product that isn't in it yet."

    def add_arguments(self, parser):
        parser.add_argument("product_slug")
        parser.add_argument("kb_slug")

    def handle(self, *args, product_slug, kb_slug, **options):
        if kb_slug == DEFAULT_AUDIENCE_SLUG:
            raise CommandError(f"{kb_slug!r} is the default knowledge base.")

        try:
            product = Product.objects.get(slug=product_slug)
        except Product.DoesNotExist:
            raise CommandError(f"Unknown product: {product_slug!r}")

        try:
            kb = Audience.objects.get(slug=kb_slug)
        except Audience.DoesNotExist:
            raise CommandError(f"Unknown knowledge base: {kb_slug!r}")

        # One add() per article keeps the signals that re-render it and clear its caches.
        documents = list(
            Document.objects.filter(parent__isnull=True, products=product).exclude(audiences=kb)
        )
        for document in documents:
            document.audiences.add(kb)

        self.stdout.write(f"Articles added to {kb.slug}: {len(documents)}")
