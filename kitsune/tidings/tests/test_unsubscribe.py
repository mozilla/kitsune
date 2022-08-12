from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.tidings.tests import WatchFactory


class UnsubscribeTests(TestCase):
    def test_view_get(self):
        watch = WatchFactory()

        url = reverse("tidings.unsubscribe", args=(watch.id,))
        resp = self.client.get(url, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed("tidings/unsub.html")

    def test_view_post_success(self):
        watch = WatchFactory(secret="ou812")

        url = reverse("tidings.unsubscribe", args=(watch.id,), locale="en-US")
        resp = self.client.post(url + "?s={0}".format(watch.secret))

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed("tidings/unsubscribe_success.html")

    def test_view_post_error_wrong_doesnotexist(self):
        url = reverse("tidings.unsubscribe", args=(42,), locale="en-US")
        resp = self.client.post(url + "?s=applesandcinnamon")

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed("tidings/unsubscribe_error.html")

    def test_view_post_error_wrong_secret(self):
        watch = WatchFactory(secret="ou812")
        url = reverse("tidings.unsubscribe", args=(watch.id,), locale="en-US")
        resp = self.client.post(url + "?s=applesandcinnamon")

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed("tidings/unsubscribe_error.html")
