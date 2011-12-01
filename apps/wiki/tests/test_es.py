from wiki.tests import ESTestCase, document
from wiki.models import Document

import elasticutils
import uuid

from nose.tools import eq_


class TestPostUpdate(ESTestCase):
    def test_added(self):
        # Use a uuid since it's "unique" and makes sure we're not
        # accidentally picking up a Post we don't want.
        title = str(uuid.uuid4())

        doc = document(title=title)

        original_count = elasticutils.S(Document).count()

        doc.save()
        self.refresh()

        eq_(elasticutils.S(Document).count(), original_count + 1)

    def test_deleted(self):
        # Use a uuid since it's "unique" and makes sure we're not
        # accidentally picking up a Post we don't want.
        title = str(uuid.uuid4())

        doc = document(title=title)

        # Assert that it's not in the index before saving.
        eq_(elasticutils.S(Document).query(title=title).count(), 1)

        doc.delete()

        eq_(elasticutils.S(Document).query(title=title).count(), 0)
