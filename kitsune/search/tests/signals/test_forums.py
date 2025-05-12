from kitsune.search.tests import Elastic7TestCase
from kitsune.forums.tests import PostFactory
from elasticsearch.exceptions import NotFoundError

from kitsune.search.documents import ForumDocument


class ForumDocumentSignalsTests(Elastic7TestCase):
    def setUp(self):
        self.post = PostFactory()
        self.post_id = self.post.id

    def get_doc(self):
        return ForumDocument.get(self.post_id)

    def test_post_save(self):
        self.post.content = "foobar"
        self.post.save()

        self.assertEqual(self.get_doc().content, "foobar")

    def test_thread_save(self):
        thread = self.post.thread
        thread.title = "foobar"
        thread.save()

        self.assertEqual(self.get_doc().thread_title, "foobar")

    def test_post_delete(self):
        self.post.delete()

        with self.assertRaises(NotFoundError):
            self.get_doc()

    def test_thread_delete(self):
        self.post.thread.delete()

        with self.assertRaises(NotFoundError):
            self.get_doc()
