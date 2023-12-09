from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


class TestDocumentViews(TestCase):
    def setUp(self):
        super().setUp()
        self.group1 = GroupFactory(name="group1")
        self.user1 = UserFactory(groups=[self.group1])
        self.staff = UserFactory(is_staff=True)
        self.doc1 = DocumentFactory()
        self.doc2 = ApprovedRevisionFactory().document
        self.doc3 = ApprovedRevisionFactory(document__restrict_to_staff=True).document
        self.doc4 = ApprovedRevisionFactory(document__restrict_to_group=self.group1).document

    def test_anonymous_detail(self):
        res = self.client.get(reverse("document-detail", args=[self.doc1.slug]))
        self.assertEqual(res.status_code, 404)
        res = self.client.get(reverse("document-detail", args=[self.doc3.slug]))
        self.assertEqual(res.status_code, 404)
        res = self.client.get(reverse("document-detail", args=[self.doc4.slug]))
        self.assertEqual(res.status_code, 404)
        res = self.client.get(reverse("document-detail", args=[self.doc2.slug]))
        self.assertEqual(res.status_code, 200)
        detail = res.json()
        self.assertEqual(detail["slug"], self.doc2.slug)
        self.assertEqual(detail["title"], self.doc2.title)

    def test_restricted_visibility_detail(self):
        self.client.login(username=self.user1.username, password="testpass")
        res = self.client.get(reverse("document-detail", args=[self.doc1.slug]))
        self.assertEqual(res.status_code, 404)
        res = self.client.get(reverse("document-detail", args=[self.doc3.slug]))
        self.assertEqual(res.status_code, 404)
        res = self.client.get(reverse("document-detail", args=[self.doc2.slug]))
        self.assertEqual(res.status_code, 200)
        detail = res.json()
        self.assertEqual(detail["slug"], self.doc2.slug)
        self.assertEqual(detail["title"], self.doc2.title)
        res = self.client.get(reverse("document-detail", args=[self.doc4.slug]))
        self.assertEqual(res.status_code, 200)
        detail = res.json()
        self.assertEqual(detail["slug"], self.doc4.slug)
        self.assertEqual(detail["title"], self.doc4.title)

        self.client.login(username=self.staff.username, password="testpass")
        res = self.client.get(reverse("document-detail", args=[self.doc1.slug]))
        self.assertEqual(res.status_code, 404)
        res = self.client.get(reverse("document-detail", args=[self.doc4.slug]))
        self.assertEqual(res.status_code, 404)
        res = self.client.get(reverse("document-detail", args=[self.doc2.slug]))
        self.assertEqual(res.status_code, 200)
        detail = res.json()
        self.assertEqual(detail["slug"], self.doc2.slug)
        self.assertEqual(detail["title"], self.doc2.title)
        res = self.client.get(reverse("document-detail", args=[self.doc3.slug]))
        self.assertEqual(res.status_code, 200)
        detail = res.json()
        self.assertEqual(detail["slug"], self.doc3.slug)
        self.assertEqual(detail["title"], self.doc3.title)

    def test_anonymous_list(self):
        res = self.client.get(reverse("document-list"))
        self.assertEqual(res.status_code, 200)
        result = res.json()
        self.assertEqual(result["count"], 1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["slug"], self.doc2.slug)
        self.assertEqual(result["results"][0]["title"], self.doc2.title)

    def test_restricted_visibility_list(self):
        self.client.login(username=self.user1.username, password="testpass")
        res = self.client.get(reverse("document-list"))
        self.assertEqual(res.status_code, 200)
        # Only the documents visible to user1 should be present.
        result = res.json()
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(
            set(d["slug"] for d in result["results"]), set((self.doc2.slug, self.doc4.slug))
        )
        self.assertEqual(
            set(d["title"] for d in result["results"]), set((self.doc2.title, self.doc4.title))
        )

        self.client.login(username=self.staff.username, password="testpass")
        res = self.client.get(reverse("document-list"))
        self.assertEqual(res.status_code, 200)
        # Only the documents visible to staff should be present.
        result = res.json()
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(
            set(d["slug"] for d in result["results"]), set((self.doc2.slug, self.doc3.slug))
        )
        self.assertEqual(
            set(d["title"] for d in result["results"]), set((self.doc2.title, self.doc3.title))
        )
