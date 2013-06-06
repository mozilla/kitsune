from django.contrib.auth.models import AnonymousUser

import mock
from nose.tools import eq_
from test_utils import RequestFactory

from kitsune import messages
from kitsune.messages.context_processors import unread_message_count
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import user


class UnreadCountTests(TestCase):
    """Tests for unread_message_count."""

    @mock.patch.object(messages, 'unread_count_for')
    def test_anonymous(self, unread_count_for):
        """Test anonymous user with flag active."""
        unread_count_for.return_value = 3
        rf = RequestFactory()
        request = rf.get('/')
        request.user = AnonymousUser()
        eq_(0, unread_message_count(request)['unread_message_count'])
        assert not unread_count_for.called

    @mock.patch.object(messages, 'unread_count_for')
    def test_authenticated(self, unread_count_for):
        """Test authenticated user with flag active."""
        unread_count_for.return_value = 3
        rf = RequestFactory()
        request = rf.get('/')
        request.user = user(save=True)
        eq_(3, unread_message_count(request)['unread_message_count'])
        assert unread_count_for.called
