from nose.tools import eq_

from notifications.models import Watch
from notifications.tests import watch
from sumo.helpers import urlparams
from sumo.tests import TestCase
from sumo.urlresolvers import reverse


FAILURE_STRING = 'We could not find your subscription'


class UnsubscribeTests(TestCase):
    """Integration tests for unsubscribe view"""

    def test_confirmation(self):
        """Ensure the confirmation page renders if you feed it valid data."""
        w = watch(save=True)
        response = self.client.get(
            urlparams(reverse('notifications.unsubscribe',
                              locale='en-US',
                              args=[w.pk]),
                      s=w.secret))
        self.assertContains(response, 'Are you sure you want to unsubscribe?')

    def test_no_such_watch(self):
        """Assert it complains when asked for a nonexistent Watch."""
        for method in [self.client.get, self.client.post]:
            response = method(reverse('notifications.unsubscribe',
                                      locale='en-US',
                                      args=[33]))
            self.assertContains(response, FAILURE_STRING)

    def test_no_secret(self):
        """Assert it complains when no secret is given."""
        w = watch(save=True)
        for method in [self.client.get, self.client.post]:
            response = method(reverse('notifications.unsubscribe',
                                      locale='en-US',
                                      args=[w.pk]))
            self.assertContains(response, FAILURE_STRING)

    def test_wrong_secret(self):
        """Assert it complains when an incorrect secret is given."""
        w = watch(save=True)
        for method in [self.client.get, self.client.post]:
            response = method(
                urlparams(reverse('notifications.unsubscribe',
                                  locale='en-US',
                                  args=[w.pk]),
                          s='WRONGwrong'))
            self.assertContains(response, FAILURE_STRING)

    def test_success(self):
        """Ensure the watch deletes and view says "yay" when all goes well."""
        w = watch(save=True)
        response = self.client.post(
            urlparams(reverse('notifications.unsubscribe',
                              locale='en-US',
                              args=[w.pk]),
                      s=w.secret))
        self.assertContains(response, '<h1>Unsubscribed</h1>')
        eq_(0, Watch.objects.count())
