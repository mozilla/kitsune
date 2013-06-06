from kitsune.karma.actions import KarmaAction
from kitsune.karma.manager import KarmaManager


class AnswerAction(KarmaAction):
    """The user posted an answer."""
    action_type = 'answer'
    default_points = 1


class FirstAnswerAction(KarmaAction):
    """The user posted the first answer to a question."""
    action_type = 'first-answer'
    default_points = 5


class AnswerMarkedHelpfulAction(KarmaAction):
    """The user's answer was voted as helpful."""
    action_type = 'helpful-answer'
    default_points = 10


class AnswerMarkedNotHelpfulAction(KarmaAction):
    """The user's answer was voted as not helpful."""
    action_type = 'nothelpful-answer'
    default_points = -10


class SolutionAction(KarmaAction):
    """The user's answer was marked as the solution."""
    action_type = 'solution'
    default_points = 25


KarmaManager.register(AnswerAction)
KarmaManager.register(FirstAnswerAction)
KarmaManager.register(AnswerMarkedHelpfulAction)
KarmaManager.register(AnswerMarkedNotHelpfulAction)
KarmaManager.register(SolutionAction)
