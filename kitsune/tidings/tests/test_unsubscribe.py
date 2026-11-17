from kitsune.sumo.tests import TestCase, template_used
from kitsune.sumo.urlresolvers import reverse
from kitsune.tidings.models import Watch
from kitsune.tidings.tests import WatchFactory


class UnsubscribeTests(TestCase):
    def test_view_get(self):
        watch = WatchFactory(secret="ou812")

        url = reverse("tidings.unsubscribe", args=(watch.id,), locale="en-US")
        resp = self.client.get(url + "?s={}".format(watch.secret))

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(template_used(resp, "tidings/unsub.html"))
        self.assertTrue(Watch.objects.filter(pk=watch.pk).exists())

    def test_view_post_success(self):
        watch = WatchFactory(secret="ou812")

        url = reverse("tidings.unsubscribe", args=(watch.id,), locale="en-US")
        resp = self.client.post(url + "?s={}".format(watch.secret))

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(template_used(resp, "tidings/unsubscribe_success.html"))
        self.assertFalse(Watch.objects.filter(pk=watch.pk).exists())

    def test_view_post_error_wrong_doesnotexist(self):
        url = reverse("tidings.unsubscribe", args=(42,), locale="en-US")
        resp = self.client.post(url + "?s=applesandcinnamon")

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(template_used(resp, "tidings/unsubscribe_error.html"))

    def test_view_post_error_wrong_secret(self):
        watch = WatchFactory(secret="ou812")
        url = reverse("tidings.unsubscribe", args=(watch.id,), locale="en-US")
        resp = self.client.post(url + "?s=applesandcinnamon")

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(template_used(resp, "tidings/unsubscribe_error.html"))
        self.assertTrue(Watch.objects.filter(pk=watch.pk).exists())
