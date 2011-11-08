from karma.actions import KarmaAction


class TestAction1(KarmaAction):
    """A test action for testing!"""
    action_type = 'test-action-1'
    points = 3


class TestAction2(KarmaAction):
    """Another test action for testing!"""
    action_type = 'test-action-2'
    points = 7
