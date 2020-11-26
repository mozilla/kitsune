from kitsune.search.v2.tests import Elastic7TestCase
from kitsune.users.tests import UserFactory, GroupFactory
from kitsune.products.tests import ProductFactory

from kitsune.search.v2.documents import ProfileDocument
from elasticsearch7.exceptions import NotFoundError


class ProfileDocumentSignalsTests(Elastic7TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.user_id = self.user.id

    @property
    def _doc(self):
        return ProfileDocument.get(self.user_id)

    def test_user_save(self):
        self.user.username = "jdoe"
        self.user.save()

        self.assertEqual(self._doc.username, "jdoe")

    def test_profile_save(self):
        profile = self.user.profile
        profile.locale = "foobar"
        profile.save()

        self.assertEqual(self._doc.locale, "foobar")

    def test_user_groups_change(self):
        group = GroupFactory()
        self.user.groups.add(group)

        self.assertIn(group.id, self._doc.group_ids)

        self.user.groups.remove(group)

        self.assertNotIn(group.id, self._doc.group_ids)

    def test_user_products_change(self):
        profile = self.user.profile
        product = ProductFactory()
        profile.products.add(product)

        self.assertIn(product.id, self._doc.product_ids)

        profile.products.remove(product)

        self.assertNotIn(product.id, self._doc.product_ids)

    def test_user_delete(self):
        self.user.delete()

        with self.assertRaises(NotFoundError):
            self._doc

    def test_profile_delete(self):
        self.user.profile.delete()

        with self.assertRaises(NotFoundError):
            self._doc

    def test_group_delete(self):
        group = GroupFactory()
        self.user.groups.add(group)
        group.delete()

        self.assertEqual(self._doc.group_ids, [])

    def test_product_delete(self):
        profile = self.user.profile
        product = ProductFactory()
        profile.products.add(product)
        product.delete()

        self.assertEqual(self._doc.product_ids, [])
