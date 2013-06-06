# -*- coding: utf-8 -*-
from nose.tools import eq_

from kitsune import urls
from kitsune.sumo.tests import TestCase
from kitsune.wiki.admin import DocumentAdmin
from kitsune.wiki.models import Document
from kitsune.wiki.tests import document, translated_revision


class ArchiveTests(TestCase):
    """Tests for the archival bit flipping in the admin UI"""

    def test_inheritance(self):
        """Make sure parent/child equality of is_archived is maintained."""
        # Set up a child and a parent and an orphan (all false) and something
        # true.
        translated_revision(save=True)
        translated_revision(save=True)
        document(save=True)
        document(is_archived=True, save=True)

        # Batch-clear the archival bits:
        DocumentAdmin._set_archival(Document.objects.all(), True)

        # Assert the child of the parent and the parent of the child (along
        # with everything else) became (or stayed) true:
        eq_(Document.objects.filter(is_archived=True).count(), 6)
        # We didn't lose any, and they're all true.
