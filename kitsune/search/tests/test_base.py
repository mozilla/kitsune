from django.test.utils import override_settings
from kitsune.search.tests import Elastic7TestCase
from kitsune.search.documents import ProfileDocument
from kitsune.users.tests import ProfileFactory, GroupFactory
from elasticsearch.helpers import bulk as es7_bulk
from kitsune.search.es7_utils import es7_client


@override_settings(ES_LIVE_INDEXING=False)
class ToActionTests(Elastic7TestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        group = GroupFactory()
        self.profile.user.groups.add(group)
        self.prepare().save()
        self.profile.user.groups.remove(group)

    def prepare(self):
        return ProfileDocument.prepare(self.profile)

    @property
    def doc(self):
        return ProfileDocument.get(self.profile.pk)

    def test_index_empty_list(self):
        self.prepare().to_action("index")
        self.assertEqual(self.doc.group_ids, [])

    def test_index_bulk_empty_list(self):
        payload = self.prepare().to_action("index", is_bulk=True)
        es7_bulk(es7_client(), [payload])
        self.assertEqual(self.doc.group_ids, [])

    def test_update_empty_list(self):
        self.prepare().to_action("update")
        self.assertEqual(self.doc.group_ids, None)

    def test_update_bulk_empty_list(self):
        payload = self.prepare().to_action("update", is_bulk=True)
        es7_bulk(es7_client(), [payload])
        self.assertEqual(self.doc.group_ids, [])
