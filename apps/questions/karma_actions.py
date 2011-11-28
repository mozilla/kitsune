from karma.actions import KarmaAction
from karma.manager import KarmaManager


class AnswerAction(KarmaAction):
    """The user posted an answer."""
    action_type = 'answer'
    points = 1


class FirstAnswerAction(KarmaAction):
    """The user posted the first answer to a question."""
    action_type = 'first-answer'
    points = 5


class AnswerMarkedHelpfulAction(KarmaAction):
    """The user's answer was voted as helpful."""
    action_type = 'helpful-answer'
    points = 10


class AnswerMarkedNotHelpfulAction(KarmaAction):
    """The user's answer was voted as not helpful."""
    action_type = 'nothelpful-answer'
    points = -10


class SolutionAction(KarmaAction):
    """The user's answer was marked as the solution."""
    action_type = 'solution'
    points = 25


KarmaManager.register(AnswerAction)
KarmaManager.register(FirstAnswerAction)
KarmaManager.register(AnswerMarkedHelpfulAction)
KarmaManager.register(AnswerMarkedNotHelpfulAction)
KarmaManager.register(SolutionAction)
