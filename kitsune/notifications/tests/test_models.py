from datetime import datetime

from nose.tools import eq_

from kitsune.notifications.tests import notification
from kitsune.sumo.tests import TestCase


class TestNotificationModel(TestCase):

    def test_is_read_false(self):
        n = notification(read_at=None, save=True)
        eq_(n.is_read, False)

    def test_is_read_true(self):
        n = notification(read_at=datetime.now(), save=True)
        eq_(n.is_read, True)

    def test_set_is_read_true(self):
        n = notification(read_at=None, save=True)
        n.is_read = True
        assert n.read_at is not None

    def test_set_is_read_false(self):
        n = notification(read_at=datetime.now(), save=True)
        n.is_read = False
        assert n.read_at is None
