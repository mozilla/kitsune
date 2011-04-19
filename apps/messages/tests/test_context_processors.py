from django.contrib.auth.models import AnonymousUser

import mock
from nose.tools import eq_
from test_utils import RequestFactory
import waffle

import messages
from messages.context_processors import unread_message_count
from sumo.tests import TestCase, get_user


class UnreadCountTests(TestCase):
    """Tests for unread_message_count."""

    fixtures = ['users.json']

    @mock.patch.object(messages, 'unread_count_for')
    @mock.patch.object(waffle, 'flag_is_active')
    def test_anonymous(self, flag_is_active, unread_count_for):
        """Test anonymous user with flag active."""
        unread_count_for.return_value = 3
        flag_is_active.return_value = True
        rf = RequestFactory()
        request = rf.get('/')
        request.user = AnonymousUser()
        eq_(0, unread_message_count(request)['unread_message_count'])
        assert not unread_count_for.called

    @mock.patch.object(messages, 'unread_count_for')
    @mock.patch.object(waffle, 'flag_is_active')
    def test_authenticated(self, flag_is_active, unread_count_for):
        """Test authenticated user with flag active."""
        unread_count_for.return_value = 3
        flag_is_active.return_value = True
        rf = RequestFactory()
        request = rf.get('/')
        request.user = get_user('rrosario')
        eq_(3, unread_message_count(request)['unread_message_count'])
        assert unread_count_for.called
    test_authenticated.xx = 1

    @mock.patch.object(messages, 'unread_count_for')
    @mock.patch.object(waffle, 'flag_is_active')
    def test_flag_off(self, flag_is_active, unread_count_for):
        """Test authenticated user with flag inactive."""
        unread_count_for.return_value = 3
        flag_is_active.return_value = False
        rf = RequestFactory()
        request = rf.get('/')
        request.user = get_user('rrosario')
        eq_(0, unread_message_count(request)['unread_message_count'])
        assert not unread_count_for.called
