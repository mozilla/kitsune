import difflib

from django.core.management.base import BaseCommand
from kitsune.wiki.models import Document
from kitsune.wiki.parser import wiki_to_html


class Command(BaseCommand):
    help = "Diffs the current wiki parsing code with the stored html in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--document-id",
            type=int,
            default=None,
            help="Diff just one document",
        )

    def handle(self, *args, **options):
        documents = Document.objects
        if doc_id := options["document_id"]:
            documents = documents.filter(pk=doc_id)
        else:
            documents = documents.all()
        for document in documents:
            if not document.current_revision:
                continue
            try:
                diff = difflib.ndiff(
                    document.html.split("\n"),
                    wiki_to_html(
                        document.current_revision.content,
                        locale=document.locale,
                    ).split("\n"),
                )
                diff_lines = "\n".join(filter(lambda x: not x.startswith("  "), diff))
                if diff_lines:
                    print(f"DOCUMENT_ID: {document.id}")
                    print(diff_lines)
            except Exception as e:
                if doc_id:
                    raise e
                print(f"DOCUMENT_ID EXCEPTION: {document.id}")
                print(f"{type(e)}: {e}")
