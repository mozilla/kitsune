import uuid

import elasticutils
from nose.tools import eq_

from sumo.tests import ElasticTestCase
from wiki.tests import document
from wiki.models import Document


class TestPostUpdate(ElasticTestCase):
    def test_add_and_delete(self):
        """Adding a doc should add it to the search index; deleting should
        delete it."""
        doc = document(save=True)
        self.refresh()
        eq_(elasticutils.S(Document).count(), 1)

        doc.delete()
        self.refresh()
        eq_(elasticutils.S(Document).count(), 0)
