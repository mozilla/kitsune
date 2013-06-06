from kitsune.karma.actions import KarmaAction
from kitsune.karma.manager import KarmaManager


class TestAction1(KarmaAction):
    """A test action for testing!"""
    action_type = 'test-action-1'
    default_points = 3


class TestAction2(KarmaAction):
    """Another test action for testing!"""
    action_type = 'test-action-2'
    default_points = 7


KarmaManager.action_types = {}  # Clear them out for tests.
KarmaManager.register(TestAction1)
KarmaManager.register(TestAction2)
