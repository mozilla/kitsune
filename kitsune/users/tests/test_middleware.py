from django.http import HttpResponsePermanentRedirect

import mobility
from nose.tools import eq_
from test_utils import RequestFactory

from kitsune.sumo.tests import TestCase
from kitsune.users.middleware import LogoutDeactivatedUsersMiddleware
from kitsune.users.tests import user


class LogoutDeactivatedUsersMiddlewareTestCase(TestCase):
    def test_inactive_user_is_logged_out(self):
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')

        # Verify that active user works fine.
        response = self.client.get('/en-US/home')
        eq_(200, response.status_code)
        assert (u.username in response.content)

        # Deactivate the user and verify he is logged out.
        u.is_active = False
        u.save()
        response = self.client.get('/en-US/home', follow=True)
        eq_(200, response.status_code)
        assert u.username not in response.content
