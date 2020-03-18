from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory

import mock
from nose.tools import eq_

from kitsune.messages import context_processors
from kitsune.messages.context_processors import unread_message_count
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class UnreadCountTests(TestCase):
    """Tests for unread_message_count."""

    @mock.patch.object(context_processors, "unread_count_for")
    def test_anonymous(self, unread_count_for):
        """Test anonymous user."""
        unread_count_for.return_value = 3
        rf = RequestFactory()
        request = rf.get("/")
        request.user = AnonymousUser()
        eq_(0, unread_message_count(request)["unread_message_count"])
        assert not unread_count_for.called

    @mock.patch.object(context_processors, "unread_count_for")
    def test_authenticated(self, unread_count_for):
        """Test authenticated user."""
        unread_count_for.return_value = 3
        rf = RequestFactory()
        request = rf.get("/")
        request.user = UserFactory()
        eq_(3, unread_message_count(request)["unread_message_count"])
        assert unread_count_for.called
